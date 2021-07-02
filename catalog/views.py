from django.contrib.auth import models
from django.shortcuts import get_object_or_404, render
from django.views import generic
from .models import Book, Author, Language, BookInstance, Genre
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin

import datetime
from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponseRedirect
from django.urls import reverse

from catalog.forms import RenewBookForm

from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from catalog.models import Author, Book

# Create your views here.
def index(request):
    #Generate counts of some of the main objects
    num_books = Book.objects.all().count()
    num_instances = BookInstance.objects.all().count()
    #Number of visits (Sessions Framework)

    num_visits = request.session.get('num_visits', 0)
    request.session['num_visits'] = num_visits + 1    
    #Available books
    num_instances_available = BookInstance.objects.filter(status__exact='a').count()

    #Available genres
    num_genres_available = Genre.objects.count()

    #The all is implied by default
    num_authors = Author.objects.count()

    #Books that contain 'the'
    books_with_the = Book.objects.filter(title__icontains='the')

    context = {
        'num_books': num_books,
        'num_instances': num_instances,
        'num_instances_available': num_instances_available,
        'num_authors': num_authors,
        'num_genres_available': num_genres_available,
        'num_visits': num_visits,
        'books_with_the': books_with_the,
    }

    #render the html template index.html with the data in the context variable
    return render(request, 'index.html', context=context)

class BookListView(generic.ListView):
    model = Book
    paginate_by = 2
    
class BookDetailView(generic.DetailView):
    model=Book

class AuthorListView(generic.ListView):
    model = Author
    paginate_by = 2

class AuthorDetailView(generic.DetailView):
    model = Author

class LoanedBookByUserListView(LoginRequiredMixin,generic.ListView):
    model = BookInstance
    template_name = 'catalog/bookinstance_list_borrowed_user.html'
    paginate_by = 10

    def get_queryset(self):
        return BookInstance.objects.filter(borrower=self.request.user).filter(status__exact='o').order_by('due_back')

class LibrarianLoanedBooksLiistView(PermissionRequiredMixin,generic.ListView):
    permission_required = 'catalog.can_mark_returned'
    model = BookInstance
    template_name = 'catalog/bookinstance_list_librarian.html'
    paginate_by = 10

    def get_queryset(self):
        return BookInstance.objects.filter(status__exact='o').order_by('due_back')

@login_required
@permission_required('catalog.can_mark_returned', raise_exception=True)
def renew_book_librarian(request, pk):

    book_instance = get_object_or_404(BookInstance, pk=pk)

    #if this is a post request then process the form data
    if request.method == 'POST':

        #create a form instance and populate it with data from the request (binding)
        form = RenewBookForm(request.POST)

        #check if the form is valid
        if form.is_valid():

            #process the data in cleaned form 
            book_instance.due_back = form.cleaned_data['renewal_date']
            book_instance.save()

            #redirect to anew url
            return HttpResponseRedirect(reverse('all-borrowed'))

    else:
           proposed_renewal_date = datetime.date.today() + datetime.timedelta(weeks=3)
           form = RenewBookForm(initial={'renewal_date': proposed_renewal_date})

    context = {
        'form': form,
        'book_instance': book_instance,
    }

    return render(request, 'catalog/book_renew_librarian.html', context)

class AuthorCreate(PermissionRequiredMixin,CreateView):
    permission_required = 'catalog.can_mark_returned'
    model = Author
    fields = ['first_name','last_name','date_of_birth','date_of_death']
    initial = {'date_of_death': '11/06/2020'}

class AuthorUpdate(PermissionRequiredMixin,UpdateView):
    permission_required = 'catalog.can_mark_returned'
    model = Author
    fields = '__all__' #not recommended from security pov. can cause errors if more fields are added

class AuthorDelete(PermissionRequiredMixin,DeleteView):
    permission_required = 'catalog.can_mark_returned'
    model = Author
    success_url = reverse_lazy('authors')

class BookCreate(PermissionRequiredMixin,CreateView):
    permission_required = 'catalog.can_mark_returned'
    model = Book
    fields = ['title','author','summary','isbn','genre','language']

class BookUpdate(PermissionRequiredMixin,UpdateView):
    permission_required = 'catalog.can_mark_returned'
    model = Book
    fields = '__all__'

class BookDelete(PermissionRequiredMixin,DeleteView):
    permission_required = 'catalog.can_mark_returned'
    model = Book
    success_url = reverse_lazy('books')