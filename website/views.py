from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from website.models import *
import random

# Create your views here.


def home(request):
	books = list(Book.objects.all())
	random.shuffle(books)
	sixbooks = books[:6]
	return render(request, 'homepage.html', {'books': sixbooks})


def lend(request):
	if request.method == "GET":
		return render(request, 'new_lend.html', {})
	if request.method == "POST":
		name = request.POST['name']
		condition = request.POST['condition']
		desc = request.POST['desc']
		tfl = request.POST['tfl']
		url = request.POST['url']
		book = Book.objects.filter(name=name)[0]
		lendituser = LenditUser.objects.filter(user=request.user)[0]
		UserBook(desc=desc, lending_time=tfl, image_url=url, condition=condition, orig_book=book, user=lendituser).save()
		return HttpResponseRedirect("/profile/"+str(lendituser.id))


def book(request, pk):
	book = Book.objects.filter(id=pk)[0]
	user_books = list(UserBook.objects.filter(orig_book=book))
	return render(request, 'book_page.html', {'book': book, 'userbooks': user_books})


def user_book(request, user_pk, book_pk):
	book = Book.objects.filter(id=book_pk)[0]
	lender = LenditUser.objects.filter(id=user_pk)[0]
	userbook = UserBook.objects.filter(user=lender, orig_book=book)[0]
	notif = Borrowed.objects.filter(user=request.user.lendituser, lender=lender, book=userbook),
	return render(request, 'user_book.html', {'book': userbook, 'lender': lender, 'notif': notif})


def profile(request, pk):
	lendituser = LenditUser.objects.filter(id=pk)[0]
	if request.user.is_anonymous():
		return HttpResponseRedirect("/login")
	self_profile = request.user == lendituser.user
	user_books = UserBook.objects.filter(user=lendituser)
	borrowed_or_not = []
	for i in user_books:
		borrowed_or_not.append(Borrowed.objects.filter(user=request.user.lendituser, lender=lendituser, book=i))
	return render(request, 'profile.html', {'userbooks': user_books,
											'lenuser': lendituser,
											'self_profile': self_profile,
	                                        'borrowed_or_not': borrowed_or_not})


def request_book(request, user_pk, book_pk):
	lender = LenditUser.objects.filter(id=user_pk)[0]
	userbook = UserBook.objects.filter(id=book_pk)[0]
	Notification(user=lender, other_user=request.user.lendituser, book=userbook, type='r', desc='',read=0).save()
	Borrowed(user=request.user.lendituser, lender=lender, book=userbook, accepted=0).save()
	lender.new_notifications = lender.new_notifications + 1
	lender.save()
	return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


def notifications(request):
	notifications = Notification.objects.filter(user=request.user.lendituser).order_by('-id')
	for notification in notifications:
		notification.read = 1
	request.user.lendituser.new_notifications = 0
	request.user.lendituser.save()
	return render(request, 'notifications.html', {
		'notifications': notifications
		})


def request_handle(request):
	if request.method == 'POST':
		notification = Notification.objects.filter(pk=int(request.POST["notifid"]))[0]
		if request.POST['action'] == 'accept':
			Notification(user=notification.other_user,
						 other_user=request.user.lendituser,
						 book=notification.book,
						 type='a',
						 desc='Contact Number- ' + str(request.POST["phno"]) \
						 	  +'\nMessage- ' + (request.POST["message"]),
						 read=0).save()
			notification.other_user.new_notifications += 1
			notification.other_user.save()
			borrowed_entry = Borrowed.objects.filter(user=notification.other_user,
													 lender=request.user.lendituser,
													 book=notification.book)[0]
			borrowed_entry.accepted = 1
			borrowed_entry.save()
			notification.book.status = 'Lent'
			notification.book.save()
			notification.delete()
		if request.POST['action'] == 'decline':
			Notification(user=notification.other_user,
						 other_user=request.user.lendituser,
						 book=notification.book,
						 type='d',
						 desc='',
						 read=0).save()
			notification.other_user.new_notifications += 1
			notification.other_user.save()
			borrowed_entry = Borrowed.objects.filter(user=notification.other_user,
													 lender=request.user.lendituser,
													 book=notification.book)[0]
			borrowed_entry.delete()
			notification.delete()
		return HttpResponse("Handled")