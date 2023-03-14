from django.contrib.auth.decorators import login_required
from django.contrib import auth
from django.shortcuts import render,redirect
from django.contrib import messages
from .forms import  CategoriesForm
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from .models import User, Categories
from django.core.paginator import Paginator
import datetime


from .models import User, Categories, SpendingFile, Reward, Budget, RewardPoint, DeliveryAddress
from .forms import *
from django.views import View
from django.utils.decorators import method_decorator
from pst.helpers.auth import login_prohibited
from django.contrib.auth import authenticate, login, logout

import os
from NewHappy.settings import MEDIA_ROOT
from django.http import HttpResponse
import random
import nltk
nltk.download('punkt')
nltk.download('wordnet')
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from django.db.models import Sum

# Create your views here.


@login_required
def user_feed(request):
    return render(request, 'user_feed.html')
    
def visitor_signup(request):
    if request.method == 'POST':
        form = VisitorSignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth.login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            return redirect('home')
        else:
            return render(request, 'visitor_signup.html', {'form': form})
    else:
        form = VisitorSignupForm()
        return render(request, 'visitor_signup.html', {'form': form})


@login_required
def home(request):
    return render(request, 'home.html')

@login_prohibited
def visitor_introduction(request):
    return render(request, 'visitor_introduction.html')

@login_prohibited
def log_in(request):
    if request.method == 'POST':
        next = request.POST.get('next') or ''
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password')
            user = authenticate(username=email, password=password)
            if user is not None:
                login(request, user)
                redirect_url = next or 'home'
                return redirect(redirect_url)
       # messages.add_message(request, messages.ERROR,
                            # "The credentials provided are invalid!")
        else:
            next = request.GET.get('next') or ''
    form = LoginForm()
    return render(request, 'log_in.html', {'form': form})


def log_out(request):
    logout(request)
    return redirect('visitor_introduction')

#Chatbot is a simple virtual help assistant that can answer user's question base on keywords
def chat_bot(request):
    chat_history = [] # this is use to store all the chat history between user and chatbot
    if request.method == 'POST':
        user_input = request.POST['user_input']
        chat_bot_response = respond(user_input)
        chat_history.append((user_input, chat_bot_response))
        return render(request, 'chat_bot.html', {'chat_history': chat_history})
    return render(request, 'chat_bot.html', {'chat_history': chat_history})

def respond(user_input):
    lemmatizer = WordNetLemmatizer()
    keywords = {
        "pst": ["personal spending tracker", "pst"],
        "budget": ["budget", "spending budget", "financial budget"],
        "expense": ["expense", "spending", "financial expense"],
        "track": ["track", "record", "keep track"],
        "saving": ["saving", "save", "financial saving"],
        "finance": ["finance", "financial management", "money management"],
        "hello": ["hi", "hello", "hey", "greetings", "heya", "hola", "what's up", "sup"],
        "bye": ["bye", "goodbye", "see you later", "adios", "later", "farewell"]
    }

    responses = {
        "pst": ["Our Personal Spending Tracker helps you keep track of your daily expenses and budget."], 
        "budget": ["You can use our Personal Spending Tracker to set budgets for different categories of expenses."], 
        "expense": ["You can log all your expenses on our Personal Spending Tracker, including the date, category, and amount spent. Would you like help tracking an expense?"], 
        "track": ["Our Personal Spending Tracker is designed to help you keep track of your daily expenses, budget, and savings."], 
        "saving": ["Our Personal Spending Tracker can help you track your savings and keep you on track to reach your financial goals."], 
        "finance": ["With the PSC, you can take control of your personal finances and make informed decisions about your spending and saving."],
        "hello": ["Hello! How may I help you?"],
        "bye": ["Goodbye! Have a great day!"],
    }

    for keyword, synonyms in keywords.items():
        if user_input.lower() in [s.lower() for s in synonyms]:
            return random.choice(responses[keyword])

    tokens = word_tokenize(user_input)
    tokens = [lemmatizer.lemmatize(token.lower()) for token in tokens]

    for keyword, synonyms in keywords.items():
        for token in tokens:
            if token in synonyms:
                return random.choice(responses[keyword])
    return "Sorry, I do not understand what you mean."



@login_required
def add_spending(request):
    if request.method == 'POST':
        form = AddSpendingForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            spending = form.save(commit=False)
            spending.spending_owner = request.user
            spending.save()
            for file in request.FILES.getlist('file'):
                SpendingFile.objects.create(
                    spending = spending,
                    file = file
                )
            return redirect('home')
    else:
        form = AddSpendingForm(user=request.user)
    return render(request, 'add_spending.html',  {'form': form})


@login_required
def view_spending(request):
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if start_date and end_date:
        start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d').date()
        spending = Spending.objects.filter(date__range=[start_date, end_date]).order_by('date')
    else:
        spending = Spending.objects.all().order_by('date')

    paginator = Paginator(spending, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {'spending': spending, 'page_obj': page_obj}
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'spending_table.html', context)
    else:
        return render(request, 'view_spending.html', context)

@login_required
def add_spending_categories(request):
    if request.method == 'POST':
        form = CategoriesForm(request.POST, request.FILES)
        if form.is_valid():
            category = form.save(commit = False)
            category.owner = request.user
            category.save()
            return redirect('home')
    else:
        form = CategoriesForm()
    return render(request, 'add_spending_categories.html',  {'form': form})

@login_required
def view_spending_categories(request):
    if request.method == 'POST':
        delete_spending_categories(request)
    categories_expenditure = Categories.objects.filter(categories_type = Spending_type.EXPENDITURE, owner = request.user)
    categories_income = Categories.objects.filter(categories_type = Spending_type.INCOME, owner = request.user)
    return render(request, 'view_spending_categories.html', {'categories_expenditure': categories_expenditure, 'categories_income': categories_income})

@login_required
def delete_spending_categories(request):
    if request.method == 'POST':
        category_id = request.POST.get('category_id')
        category = Categories.objects.get(id=category_id)
        if category.default_category == False:
            category.delete()
        else:
            messages.add_message(request,messages.ERROR,"You can not delete default category!")
        return redirect('view_spending_categories')

@login_required
def update_spending_categories(request, category_id):
    category = Categories.objects.get(id=category_id)
    if request.method == 'POST':
        form = CategoriesForm(request.POST)
        if category.default_category == False:
            if form.is_valid():
                form = CategoriesForm(request.POST, instance=category)
                form.save()
                return redirect('view_spending_categories')
        else:
            messages.add_message(request,messages.ERROR,"You can not modify default category!")
            return redirect('view_spending_categories')
    else:
        category = Categories.objects.get(id=category_id)
        form = CategoriesForm(instance=category)
    return render(request, 'update_spending_categories.html', {'form': form, 'category': category})

@login_required
def user_guideline(request):
    return render(request, 'user_guideline.html')

@login_required
def set_budget(request):
    if request.method == 'POST':
        form = BudgetForm(request.POST)
        if form.is_valid():
            budget = form.save(commit=False)
            budget.budget_owner = request.user
            budget.save()
            return redirect('budget_show')
    else:
        form = BudgetForm()
    return render(request, 'budget_set.html', {'form': form})

@login_required
def show_budget(request):
    current_month = datetime.date.today().month
    total = Spending.objects.filter(
    spending_owner = request.user,
    date__month = current_month,
     spending_type = Spending_type.EXPENDITURE,
    ).aggregate(nums=Sum('amount')).get('nums')
    # total = Spending.objects.aggregate(nums=Sum('amount')).get('nums')
    budget = Budget.objects.filter(budget_owner=request.user).last()
    if budget == None:
        spending_percentage = 0
    elif total == None:
        messages.add_message(request, messages.INFO, 'you have not spent yet')
        spending_percentage = 0
    else:
        spending_percentage = int((total / budget.limit) * 100)
        if spending_percentage >= 100:
            messages.add_message(request, messages.INFO, 'you have exceeded the limit')
    return render(request, 'budget_show.html', {'budget': budget, 'spending_percentage': spending_percentage})

# @login_required
# def cal_spending():
#      spending_total = Spending.objects.aggregate(nums=Sum('amount')).get('nums')
#      return spending_total

@login_required
def index(request):
    address = DeliveryAddress.objects.filter(user=request.user).last()
    form = AddressForm()

    if Reward.objects.count() == 0:
        Reward.objects.create(name='T-shirt', points_required=20, image='rewards/shirt.jpg')
        Reward.objects.create(name='PlayStation Store 50 GBP Gift Card', points_required=50, image='rewards/playstation_gift_card.jpg')
        Reward.objects.create(name="Xbox 10 GBP Gift Card", points_required=10, image='rewards/xbox_gift_card.jpg')
        Reward.objects.create(name="Amazon 20 GBP Gift Card", points_required=20, image='rewards/amazon_gift_card.jpg')

    rewards = Reward.objects.all()
    rewards_points = RewardPoint.objects.filter(user=request.user).first()
    context = {
        'form': form,
        'rewards': rewards,
        'reward_points': rewards_points,
        'address': address,
    }
    return render(request, 'index.html', context)

@login_required
def redeem(request, reward_id):
    reward = Reward.objects.get(id=reward_id)
    reward_points = RewardPoint.objects.filter(user=request.user).first()

    error_message = "You don't have enough reward points to redeem this reward."
    context = {
        'error_message': error_message, }

    if reward_points is None:
        # error_message = "You don't have enough reward points to redeem this reward."
        # return render(request, 'error.html', context)
        messages.add_message(request, messages.INFO, "You don't have enough reward points to redeem this reward.")
        return redirect('index')
    elif reward_points.points >= reward.points_required:
            reward_points.points -= reward.points_required
            reward_points.save()
            messages.add_message(request, messages.INFO, 'Successfully redeemed, your item will be shipped to your address.')
            return redirect('index')
    else:
        # error_message = "You don't have enough reward points to redeem this reward."
        # context = {
        #     'error_message': error_message,}
        #
        # return render(request, 'error.html', context)
        messages.add_message(request, messages.INFO, "You don't have enough reward points to redeem this reward.")
        return redirect('index')

def add_address(request):
    if request.method == 'POST':
        form = AddressForm(request.POST)

        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            address.save()
            messages.success(request, 'success')
            return redirect('index')

    else:
        form = AddressForm()
    return render(request, "index.html", {'form': form})