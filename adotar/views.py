from django.shortcuts import render, redirect
from divulgar.models import Pet, Raca
from django.contrib.messages import constants
from django.contrib import messages
from .models import PedidoAdocao
from datetime import datetime
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.http import HttpResponse

@login_required
def listar_pets(request):
    if request.method == "GET":
        pets = Pet.objects.filter(status="P")
        racas = Raca.objects.all()

        cidade = request.GET.get('cidade')
        raca_filter = request.GET.get('raca')
        if cidade:
            pets = pets.filter(cidade__icontains=cidade)

        if raca_filter:
            # zero é o valor do campo "Todas as Raças" no html
            if raca_filter != "0":
                pets = pets.filter(raca__id=raca_filter)
                raca_filter = Raca.objects.get(id=raca_filter)

        return render(request, 'listar_pets.html', {'pets': pets, 'racas': racas, 'cidade': cidade, 'raca_filter': raca_filter})


@login_required
def pedido_adocao(request, id_pet):
    pet = Pet.objects.filter(id=id_pet).filter(status='P')

    #impedir que o proprio dono do pet tente adota-lo
    if pet.first().usuario == request.user:
        messages.add_message(request, constants.WARNING, 'Você não pode adotar seu próprio PET')
        return redirect('/adotar')

    #impedir repeticao de um mesmo pedido de adocao
    pedidos_usuario_AG = PedidoAdocao.objects.filter(status='AG').filter(usuario=request.user)
    if pedidos_usuario_AG:
        messages.add_message(request, constants.WARNING, 'Você já fez um pedido de adoção deste PET, aguarde uma resposta do dono.')
        return redirect('/adotar')

    if not pet.exists():
        messages.add_message(request, constants.WARNING, 'Esse Pet já foi adotado')
        return redirect('/adotar')

    pedido = PedidoAdocao(pet=pet.first(),
                          usuario=request.user,
                          data=datetime.now())

    pedido.save()
    messages.add_message(request, constants.SUCCESS, 'Esse pedido de adoção foi realizado com sucesso')

    return redirect('/adotar')

@login_required
def processa_pedido_adocao(request, id_pedido):
    status = request.GET.get('status')
    pedido = PedidoAdocao.objects.get(id=id_pedido)
    pet = Pet.objects.get(id=pedido.pet.id)

    if status == "A":
        pedido.status = 'AP'
        pet.status = 'A'
        string = '''Olá, sua adoção foi aprovada. ...'''

    elif status == "R":
        string = '''Olá, sua adoção foi recusada. ...'''
        pedido.status = 'R'

    pedido.save()
    pet.save()

    #print(pedido.usuario.email)
    email = send_mail(
        'Sua adoção foi processada',
        string,
        "adote.pet.vikmiranda@outlook.com",
        [pedido.usuario.email,],
    )

    messages.add_message(request, constants.SUCCESS, 'Pedido de adoção processado com sucesso')
    return redirect('/divulgar/ver_pedido_adocao')