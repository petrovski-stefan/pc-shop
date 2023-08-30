from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.text import slugify


# Create your models here.


class CustomUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True, related_name='profile')
    address = models.CharField(max_length=255)
    phone = models.CharField(max_length=255)
    display_name = models.CharField(max_length=255)
    image = models.ImageField(upload_to='uploaded/', default='default.png')

    def __str__(self):
        return f"{self.display_name} ({self.user})"


class Category(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(default="", blank=True, unique=True, db_index=True)

    class Meta:
        verbose_name_plural = 'Categories'

    def __str__(self):
        return str(self.name)


class Product(models.Model):
    name = models.CharField(max_length=255)
    price = models.DecimalField(decimal_places=2, max_digits=10, validators=[MinValueValidator(0)])
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(0)])
    description = models.TextField()
    image = models.ImageField(upload_to='uploaded/')
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='products')
    created_at = models.DateTimeField(auto_now_add=True)
    sold = models.IntegerField(default=0)
    slug = models.SlugField(default="", blank=True, db_index=True)

    class Meta:
        unique_together = ['seller', 'slug']

    def calculate_average_rating(self):
        if len(self.reviews.all()) == 0:
            return 'No reviews yet'
        total = 0
        for review in self.reviews.all():
            total += review.rating
        return total / len(self.reviews.all()) if len(self.reviews.all()) > 0 else 0

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super(Product, self).save(*args, **kwargs)

    def __str__(self):
        return str(self.name)


class Order(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=100,
                              choices=[('Pending', 'Pending'),
                                       ('Processing', 'Processing'),
                                       ('Delivered', 'Delivered'),
                                       ('Cancelled', 'Cancelled')],
                              default='Pending')
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    products = models.ManyToManyField(Product, through='ProductInOrder', related_name='orders')

    def calculate_total(self):
        total = 0
        for product_in_order in self.products_in_order.all():
            total += product_in_order.subtotal()
        return total

    def __str__(self):
        return f"Order #{self.id}: {self.status} ({self.customer})"


class ProductInOrder(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='products_in_order')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def subtotal(self):
        return self.product.price * self.quantity

    class Meta:
        verbose_name_plural = 'ProductInOrder'

    def __str__(self):
        return f"{self.quantity} x {self.product.name} in Order #{self.order.id}"


class Cart(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cart')
    products = models.ManyToManyField(Product, through='ProductInCart')

    def calculate_total(self):
        total = 0
        for product_in_cart in self.products_in_cart.all():
            total += product_in_cart.subtotal()
        return total

    @property
    def total_products_quantity(self):
        return self.products_in_cart.count()

    def __str__(self):
        return f"{self.customer}'s cart"


class ProductInCart(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='products_in_cart')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def subtotal(self):
        return self.product.price * self.quantity

    class Meta:
        verbose_name_plural = 'ProductInCart'

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"


class Review(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    rating = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(null=True, blank=True)
    image = models.ImageField(upload_to='uploaded/', null=True, blank=True)

    customer = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')

    def __str__(self):
        return f"Review #{self.id}: {self.rating} stars"

    class Meta:
        unique_together = ['customer', 'product']


@receiver(post_save, sender=User)
def create_user_cart(sender, instance, created, **kwargs):
    if created:
        # print(f"Creating cart for user: {instance.user.username}")
        Cart.objects.create(customer=instance)
