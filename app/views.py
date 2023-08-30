from django.contrib.auth import logout
from django.contrib.auth.views import LoginView
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from app.forms import ProductForm, ReviewForm
from app.models import Category, Product, CustomUser, Cart, Order, ProductInOrder, ProductInCart, Review
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.contrib.auth import get_user
from django.contrib.auth.models import User


# works
def index(request):
    items = list(Product.objects.order_by('-sold')[:5])
    return render(request, 'index.html', {
        "products": items
    })


# works
def products(request):
    search_term = request.GET.get('search_term')
    if search_term:
        items = Product.objects.filter(Q(name__icontains=search_term) | Q(description__icontains=search_term))
    else:
        items = Product.objects.all()
    return render(request, 'products.html', {
        "products": items
    })


def product_detail(request, slug):
    return render(request, 'product_detail.html', {
        "product": Product.objects.get(slug=slug)
    })


# works
def categories(request):
    return render(request, 'categories.html', {
        "categories": Category.objects.all()
    })


# works
def category_list(request, slug):
    category = Category.objects.get(slug=slug)
    items = list(Product.objects.filter(category=category))

    return render(request, 'category_list.html', {
        "products": items,
        "category": category
    })


def reviews(request, slug):
    product = Product.objects.get(slug=slug)
    reviews_list = list(product.reviews.all())
    reviews_list.sort(key=lambda x: x.created_at)
    return render(request, 'product_reviews.html', {
        "product": product,
        "reviews": product.reviews.all()
    })


def seller_profile(request, seller_username):
    seller = User.objects.get(username=seller_username)
    seller_products = list(seller.products.all())

    return render(request, 'seller_profile.html', {
        "seller": seller,
        "products": seller_products,
        "s_after_apostrophe": True,
    })


@login_required
def cart(request):
    if request.user.is_authenticated:
        print("User cart: ", request.user)
        custom_user = User.objects.get(username=request.user)
        user_cart = Cart.objects.get(customer=custom_user)
        items = user_cart.products_in_cart.all()

        return render(request, 'cart.html', {
            "items": items,
            "total": user_cart.calculate_total(),
        })


class CustomLoginView(LoginView):
    def get_success_url(self):
        return '/'

    def form_valid(self, form):
        return super().form_valid(form)


def logout_view(request):
    logout(request)
    return redirect('/')


def orders(request):
    User = get_user_model()

    if request.user.is_authenticated:
        user_instance = User.objects.get(username=request.user)
        print("instance: ", user_instance)
        try:
            user_profile = User.objects.get(username=user_instance)
            print("User profile: ", user_profile)
            orders = Order.objects.filter(customer=user_profile)
            print("User orders: ", orders)
        except User.DoesNotExist:
            print("error in the orders")
            orders = []
    else:
        print("not authicated")
        orders = []
    return render(request, 'orders.html', {
        "orders": orders,
        "s_after_apostrophe": True,
    })


def add_product_to_shop(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.seller = request.user
            product.save()
        return redirect(f"/seller/{request.user.username}")
    else:
        form = ProductForm()
        return render(request, 'add_product_form.html', {
            "form": form
        })


def checkout(request):
    user_cart = Cart.objects.get(customer=request.user)
    items = user_cart.products_in_cart.all()
    Order(customer=request.user).save()
    for item in items:
        print("IN THE FOR: ", request.user.orders)
        ProductInOrder(product=item.product, order=request.user.orders.last(), quantity=item.quantity).save()
        item.product.quantity -= item.quantity
        print("111 ", item.quantity)
        item.product.sold += item.quantity
        print("222 ", item.quantity)
        item.product.save()
        print("333 ")
        item.delete()
    return redirect('/')


@login_required
def add_to_cart(request):
    print("first")
    user_cart, created = Cart.objects.get_or_create(customer=request.user)
    print("user_cart: ", user_cart)
    product = Product.objects.get(id=request.POST.get('product_id'))
    if request.POST.get('quantity'):
        quantity = int(request.POST.get('quantity'))
    else:
        quantity = 1

    # custom_user = User.objects.get(username=request.user)
    # user_cart = Cart.objects.get(customer=custom_user)
    if ProductInCart.objects.filter(product=product, cart=user_cart.id).exists():
        products_in_cart = ProductInCart.objects.get(product=product, cart=user_cart)
        products_in_cart.quantity += quantity
        products_in_cart.save()
    else:
        ProductInCart(product=product, cart=user_cart, quantity=quantity).save()
    return redirect(request.META['HTTP_REFERER'])


def add_review_to_product(request):
    product = Product.objects.get(id=request.POST.get('product_id'))
    form = ReviewForm()
    return render(request, 'add_review_form.html', {
        "product": product,
        "form": form,
    })


def save_review(request):
    form = ReviewForm(request.POST)
    review = form.save(commit=False)
    product = Product.objects.get(id=request.POST.get('product_id'))
    customer = request.user
    review.customer = customer
    review.product = product
    review.save()
    return redirect(f"/reviews/{request.POST.get('product_slug')}")
