#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from django.template import RequestContext
from django.shortcuts import render_to_response, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpResponse
from datetime import datetime

from models import Category, Page
from forms import CategoryForm, PageForm, UserForm, UserProfileForm
from rango.bing_search import run_query


def index(request):
    context = RequestContext(request)
    category_list = Category.objects.order_by('-likes')[:5]
    page_list = Page.objects.order_by('-views')[:5]
    context_dict = {'categories':category_list, 'pages':page_list}

    for category in category_list:
        category.url = encode_url(category.name)

    cat_list = get_category_list()
    context_dict['cat_list'] = cat_list
    #last_visit cookie
    if request.session.get('last_visit'):
        last_visit_time = request.session.get('last_visit')
        visits = request.session.get('visits', 0)

        # calculate time if it's more than a day. 
        if (datetime.now() - datetime.strptime(last_visit_time[:-7], "%Y-%m-%d %H:%M:%S")).seconds > 5:
            request.session['visits'] = visits + 1
            request.session['last_visit'] = str(datetime.now())

    else:
        request.session['last_visit'] = str(datetime.now())
        request.session['visits'] = 1

    return render_to_response('rango/index.html', context_dict, context)

def register(request):
    context = RequestContext(request)
    registered = False
    cat_list = get_category_list()

    if request.method == 'POST':
        user_form = UserForm(data=request.POST)
        profile_form = UserProfileForm(data=request.POST)

        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save()
            user.set_password(user.password)
            user.save()

            profile = profile_form.save(commit=False)
            profile.user = user
            if 'picture' in request.FILES:
                profile.picture = request.FILES['picture']
            profile.save()

            registered = True
        else:
            print user_form.errors, profile_form.errors
    else:
        user_form = UserForm()
        profile_form = UserProfileForm()
    return render_to_response(
            'rango/register.html', 
            {'user_form': user_form, 'profile_form':profile_form, 'cat_list':cat_list, 'registered': registered},
            context)

def search(request):
    context = RequestContext(request)
    result_list = []
    cat_list = get_category_list()

    if request.method == 'POST':
        query = request.POST['query'].strip()

        if query:
            # Run Bing function to get the results list!
            result_list = run_query(query)

    return render_to_response('rango/search.html', {'result_list': result_list, 'cat_list':cat_list}, context)

def track_url(request):
    context = RequestContext(request)
    page_id = None
    url = '/rango/'
    if request.method == 'GET':
        if 'page_id' in request.GET:
            page_id = request.GET['page_id']
            try:
                page = Page.objects.get(id=page_id)
                page.views = page.views + 1
                page.save()
                url = page.url
            except:
                pass
    return redirect(url)

def user_login(request):
    context = RequestContext(request)
    cat_list = get_category_list()
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password) #checking user/pass match

        if user is not None:
            if user.is_active:
                login(request, user)
                return HttpResponseRedirect('/rango/')
            else:
                return HttpResponse("Woops! Your Rrango ehcount is disabled.")
        else:
            print "Invalid login details: {0}, {1}".format(username, password)
            return HttpResponseRedirect('/rango/login')
    else:
      return render_to_response('rango/login.html', {'cat_list':cat_list}, context)

@login_required
def user_logout(request):
    logout(request)
    return HttpResponseRedirect('/rango/')

def about(request):
    context = RequestContext(request)
    cat_list = get_category_list()
    if request.session.get('visits'):
        count = request.session.get('visits')
    else:
        count = 0

    return render_to_response('rango/about.html', {'visits': count, 'cat_list':cat_list}, context)

def category(request, category_name_url): 
    context = RequestContext(request)
    category_name = decode_url(category_name_url)
    context_dict = {'category_name': category_name, 'category_name_url': category_name_url}
    
    cat_list = get_category_list()
    context_dict['cat_list'] = cat_list
    try:
        category = Category.objects.get(name=category_name)
        pages = Page.objects.filter(category=category)
        top_pages = Page.objects.filter(category=category).order_by('-views')[:5]
        context_dict['category'] = category
        context_dict['pages'] = pages
        context_dict['top_pages'] = top_pages
    except Category.DoesNotExist:
        pass

    if request.method == 'POST':
        query = request.POST['query'].strip()
        if query:
            result_list = run_query(query)
            context_dict['result_list'] = result_list
    return render_to_response('rango/category.html', context_dict, context)

@login_required
def like_category(request):
    context = RequestContext(request)
    cat_id = None
    if request.method == "GET":
        cat_id = request.GET['category_id']
    
    likes = 0
    if cat_id: 
        category = Category.objects.get(id=int(cat_id))
        if category:
            likes = category.likes + 1
        category.likes = likes
        category.save()

    return HttpResponse(likes)

@login_required
def add_category(request):
    context = RequestContext(request)
    cat_list = get_category_list()
    if request.method == 'POST':
        form = CategoryForm(request.POST)

        if form.is_valid():
            form.save(commit=True)
            return index(request)
        else:
            print form.errors
    else:
        form = CategoryForm()

    return render_to_response('rango/add_category.html', {'form': form, 'cat_list':cat_list}, context)

def get_category_list(max_results=0, starts_with=''):
    cat_list = []
    if starts_with:
        cat_list = Category.objects.filter(name__istartswith=starts_with)
    else:
        cat_list = Category.objects.all()

    if max_results > 0:
        if len(cat_list) > max_results:
            cat_list = cat_list[:max_results]
    for cat in cat_list:
        cat.url = encode_url(cat.name)
    
    return cat_list

def get_page_list(max_results=0, starts_with=''):
    page_list = []
    if starts_with:
        page_list = Page.objects.filter(name__istartswith=starts_with)
    else:
        page_list = Page.objects.all()

    if max_results > 0:
        if len(page_list) > max_results:
            page_list = page_list[:max_results]
    for page in page_list:
        page.url = encode_url(page.name)
    
    return page_list

def suggest_category(request):
    context = RequestContext(request)
    cat_list = []
    starts_with = ''
    if request.method == 'GET':
        starts_with = request.GET['suggestion']
    cat_list = get_category_list(8, starts_with)

    return render_to_response('rango/category_list.html', {'cat_list': cat_list }, context)

def suggest_page(request):
    context = RequestContext(request)
    page_list = []
    starts_with = ''
    if request.method == 'GET':
        starts_with = request.GET['suggestion']
    page_list = get_page_list(8, starts_with)

    return render_to_response('rango/page_list.html', {'page_list': page_list }, context)

@login_required
def profile(request):
    context = RequestContext(request)
    cat_list = get_category_list()
    context_dict = {'cat_list': cat_list}
    u = User.objects.get(username=request.user)

    try:
        up = UserProfile.objects.get(user=u)
    except:
        up = None

    context_dict['user'] = u
    context_dict['userprofile'] = up
    return render_to_response('rango/profile.html', context_dict, context)

@login_required
def add_page(request, category_name_url):
    context = RequestContext(request)
    cat_list = get_category_list()
    category_name = decode_url(category_name_url)
    if request.method == 'POST':
        form = PageForm(request.POST)

        if form.is_valid():
            page = form.save(commit=False)

            try:
                cat = Category.objects.get(name=category_name)
                page.category = cat
            except Category.DoesNotExit:
                return render_to_response('rango/add_category.html', {}, context)

            page.views = 0
            form.save(commit=True)
            page.save()
            return category(request, category_name_url)
        else:
            print form.errors
    else:
        form = PageForm()

    return render_to_response('rango/add_page.html', {'category_name_url': category_name_url, 'category_name': category_name, 'cat_list':cat_list, 'form': form}, context)

@login_required
def auto_add_page(request):
    context = RequestContext(request)
    cat_id = None
    url = None
    title = None
    context_dict = {}
    if request.method == 'GET':
        cat_id = request.GET['category_id']
        url = request.GET['url']
        title = request.GET['title']
        if cat_id:
            category = Category.objects.get(id=int(cat_id))
            p = Page.objects.get_or_create(category=category, title=title, url=url)
            pages = Page.objects.filter(category=category).order_by('-views')

            #Adds our results list to the template context under name pages. 
            context_dict['pages'] = pages

    return render_to_response('rango/page_list.html', context_dict, context)

@login_required
def restricted(request):
    context = RequestContext(request)
    cat_list = get_category_list()
    context_dict = {'cat_list': cat_list}
    return render_to_response('rango/restricted.html', context_dict, context)

# Encode and Decode Functions. 
def encode_url(category_name):
    return category_name.replace(' ', '_')
def decode_url(category_name_url):
    return category_name_url.replace('_', ' ')
