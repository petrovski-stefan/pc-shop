from django.contrib.auth import logout
from django.contrib.auth.views import LoginView
from django.shortcuts import render, redirect, get_object_or_404
from app.forms import ProductForm, ReviewForm
from app.models import Category, Product, Cart, Order, ProductInOrder, ProductInCart
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.contrib.auth.models import User


def index(request):
    items = list(Product.objects.order_by('-sold')[:5])
    context = {"products": items}
    return render(request, 'index.html', context)


class CustomLoginView(LoginView):
    def get_success_url(self):
        return '/'

    def form_valid(self, form):
        return super().form_valid(form)


def logout_view(request):
    logout(request)
    return redirect('/')


def products(request):
    search_term = request.GET.get('search_term')
    if search_term:
        items = Product.objects.filter(Q(name__icontains=search_term) | Q(description__icontains=search_term))
    else:
        items = Product.objects.all()

    context = {"products": items}
    return render(request, 'products.html', context)


def product_detail(request, slug):
    context = {"product": Product.objects.get(slug=slug)}
    return render(request, 'product_detail.html', context)


def categories(request):
    context = {"categories": Category.objects.all()}
    return render(request, 'categories.html', context)


def category_list(request, slug):
    category = Category.objects.get(slug=slug)
    items = list(Product.objects.filter(category=category))
    context = {"products": items, "category": category}
    return render(request, 'category_list.html', context)


def reviews(request, slug):
    product = Product.objects.get(slug=slug)
    reviews_list = list(product.reviews.all())
    reviews_list.sort(key=lambda x: x.created_at)
    context = {"product": product, "reviews": product.reviews.all()}
    return render(request, 'product_reviews.html', context)


def seller_profile(request, seller_username):
    seller = User.objects.get(username=seller_username)
    seller_products = list(seller.products.all())
    context = {"seller": seller, "products": seller_products, }
    return render(request, 'seller_profile.html', context)


def cart(request):
    if request.user.is_authenticated:
        custom_user = User.objects.get(username=request.user)
        user_cart = Cart.objects.get(customer=custom_user)
        items = user_cart.products_in_cart.all()
        context = {"items": items, "total": user_cart.calculate_total(), }
        return render(request, 'cart.html', context)


def orders(request):
    User = get_user_model()

    if request.user.is_authenticated:
        user_instance = User.objects.get(username=request.user)
        try:
            user_profile = User.objects.get(username=user_instance)
            orders = Order.objects.filter(customer=user_profile)
        except User.DoesNotExist:
            orders = []
    else:
        orders = []

    context = {"orders": orders}
    return render(request, 'orders.html', context)


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
        context = {"form": form}
        return render(request, 'add_product_form.html', context)


def checkout(request):
    user_cart = Cart.objects.get(customer=request.user)
    items = user_cart.products_in_cart.all()

    # Don't create the order, if the user has no items in his cart
    if len(items) == 0:
        return redirect(request.META['HTTP_REFERER'])

    Order(customer=request.user).save()
    for item in items:
        ProductInOrder(product=item.product, order=request.user.orders.last(), quantity=item.quantity).save()
        item.product.quantity -= item.quantity
        item.product.sold += item.quantity
        item.product.save()
        item.delete()
    return redirect(request.META['HTTP_REFERER'])


def add_to_cart(request):
    user_cart, created = Cart.objects.get_or_create(customer=request.user)
    product = Product.objects.get(id=request.POST.get('product_id'))

    # Prevent the users from buying their own products
    if request.user == product.seller:
        return redirect(request.META['HTTP_REFERER'])

    if request.POST.get('quantity'):
        quantity = int(request.POST.get('quantity'))
    else:
        quantity = 1

    # Prevent the users from buying more than the seller offers
    if quantity > product.quantity:
        return redirect(request.META['HTTP_REFERER'])

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
    context = {"product": product, "form": form}
    return render(request, 'add_review_form.html', context)


def save_review(request):
    form = ReviewForm(request.POST)

    # Reviews must be in the range [0,10]
    if not form.is_valid():
        print("not valid")
        return redirect(f"/reviews/{request.POST.get('product_slug')}")

    review = form.save(commit=False)
    product = Product.objects.get(id=request.POST.get('product_id'))
    customer = request.user
    review.customer = customer
    review.product = product
    review.save()
    return redirect(f"/reviews/{request.POST.get('product_slug')}")


def remove_from_cart(request, product_id):
    user_cart, created = Cart.objects.get_or_create(customer=request.user)
    product = get_object_or_404(Product, id=product_id)

    try:
        product_in_cart = ProductInCart.objects.get(product=product, cart=user_cart)
        product_in_cart.delete()
    except ProductInCart.DoesNotExist:
        pass

    return redirect('cart')
