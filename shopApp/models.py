from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.urls import reverse
from django.utils import timezone

User = get_user_model()


def get_models_for_count(*model_names):
    return [models.Count(model_name) for model_name in model_names]


def get_product_url(obj, viewname):
    ct_model = obj.__class__._meta.model_name
    return reverse(viewname, kwargs={'ct_model': ct_model, 'slug': obj.slug})


class LatestProductsManager:

    @staticmethod
    def get_products_for_main_page(*args, **kwargs):
        with_respect_to = kwargs.get('with_respect_to')
        products = []
        ct_models = ContentType.objects.filter(model__in=args)
        for ct_model in ct_models:
            model_products = ct_model.model_class()._base_manager.all().order_by('-id')[:5]
            products.extend(model_products)
        if with_respect_to:
            ct_model = ContentType.objects.filter(model=with_respect_to)
            if ct_model.exists():
                if with_respect_to in args:
                    return sorted(
                        products, key=lambda x: x.__class__._meta.model_name.startswith(with_respect_to), reverse=True
                    )
        return products


class LatestProducts:

    objects = LatestProductsManager()


class CategoryManager(models.Manager):

    CATEGORY_NAME_COUNT_NAME = {
        'Notebook': 'notebook__count',
        'Smartphone': 'smartphone__count'
    }

    def get_queryset(self):
        return super().get_queryset()

    def get_categories_for_left_sidebar(self):
        models = get_models_for_count('notebook', 'smartphone')
        qs = list(self.get_queryset().annotate(*models))
        data = [
            dict(name=c.name, url=c.get_absolute_url(), count=getattr(c, self.CATEGORY_NAME_COUNT_NAME[c.name]))
            for c in qs
        ]
        return data


class Category(models.Model):

    name = models.CharField(max_length=255, verbose_name='Kategoriya nomi')
    slug = models.SlugField(unique=True)
    objects = CategoryManager()

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('category_detail', kwargs={'slug': self.slug})


class Product(models.Model):

    class Meta:
        abstract = True
        verbose_name_plural = "Mahsulotlar"

    category = models.ForeignKey(Category, verbose_name='Категория', on_delete=models.CASCADE)
    title = models.CharField(max_length=255, verbose_name='Nomlanishi')
    slug = models.SlugField(unique=True)
    image = models.ImageField(verbose_name='Rasim')
    description = models.TextField(verbose_name='Malumotlar', null=True)
    price = models.DecimalField(max_digits=9, decimal_places=2, verbose_name='Narxi')

    def __str__(self):
        return self.title



    def get_model_name(self):
        return self.__class__.__name__.lower()


class Notebook(Product):

    class Meta:
        verbose_name_plural = "Notebook Qo'shish"

    diagonal = models.CharField(max_length=255, verbose_name='O\'lchami')
    display_type = models.CharField(max_length=255, verbose_name='Тип дисплея')
    processor_freq = models.CharField(max_length=255, verbose_name='Частота Protsessor')
    ram = models.CharField(max_length=255, verbose_name='RAM')
    video = models.CharField(max_length=255, verbose_name='Video card')
    time_without_charge = models.CharField(max_length=255, verbose_name='Akumlyator quvvati')

    def __str__(self):
        return "{} : {}".format(self.category.name, self.title)

    def get_absolute_url(self):
        return get_product_url(self, 'product_detail')


class Smartphone(Product):

    diagonal = models.CharField(max_length=255, verbose_name='O\'lchami')
    display_type = models.CharField(max_length=255, verbose_name='Тип дисплея')
    resolution = models.CharField(max_length=255, verbose_name='Ekran o\'lchami')
    accum_volume = models.CharField(max_length=255, verbose_name='Batareyka quvvati')
    ram = models.CharField(max_length=255, verbose_name='RAM')
    sd = models.BooleanField(default=True, verbose_name='Наличие SD карты')
    sd_volume_max = models.CharField(
        max_length=255, null=True, blank=True, verbose_name='Максимальный объем встраивамой памяти'
    )
    main_cam_mp = models.CharField(max_length=255, verbose_name='Orqa kamera (MP)')
    frontal_cam_mp = models.CharField(max_length=255, verbose_name='Oldi kamera (MP)')

    def __str__(self):
        return "{} : {}".format(self.category.name, self.title)

    def get_absolute_url(self):
        return get_product_url(self, 'product_detail')


class CartProduct(models.Model):

    user = models.ForeignKey('Customer', verbose_name='Sotib oluvchi', on_delete=models.CASCADE)
    cart = models.ForeignKey('Cart', verbose_name='Savatcha', on_delete=models.CASCADE, related_name='related_products')
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    qty = models.PositiveIntegerField(default=1)
    final_price = models.DecimalField(max_digits=9, decimal_places=2, verbose_name='Umumiy narx')

    def __str__(self):
        return "Mahsulot: {} (savatcha uchun)".format(self.content_object.title)

    def save(self, *args, **kwargs):
        self.final_price = self.qty * self.content_object.price
        super().save(*args, **kwargs)


class Cart(models.Model):

    owner = models.ForeignKey('Customer', null=True, verbose_name='Yaratuvchi', on_delete=models.CASCADE)
    products = models.ManyToManyField(CartProduct, blank=True, related_name='related_cart')
    total_products = models.PositiveIntegerField(default=0)
    final_price = models.DecimalField(max_digits=9, default=0, decimal_places=2, verbose_name='Umumiy narx')
    in_order = models.BooleanField(default=False)
    for_anonymous_user = models.BooleanField(default=False)

    def __str__(self):
        return str(self.id)


class Customer(models.Model):

    user = models.ForeignKey(User, verbose_name='Foydalanuvchi', on_delete=models.CASCADE)
    phone = models.CharField(max_length=20, verbose_name='Telefon raqam', null=True, blank=True)
    address = models.CharField(max_length=255, verbose_name='Manzil', null=True, blank=True)
    orders = models.ManyToManyField('Order', verbose_name='Buyurtmachi', related_name='related_order')

    def __str__(self):
        return "Sotib oluvchi: {} {}".format(self.user.first_name, self.user.last_name)


class Order(models.Model):

    STATUS_NEW = 'new'
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_READY = 'is_ready'
    STATUS_COMPLETED = 'completed'

    BUYING_TYPE_SELF = 'self'
    BUYING_TYPE_DELIVERY = 'delivery'

    STATUS_CHOICES = (
        (STATUS_NEW, 'Yangi buyurtma'),
        (STATUS_IN_PROGRESS, 'Buyurtmani yangilash'),
        (STATUS_READY, 'Buyurtma tayyor'),
        (STATUS_COMPLETED, 'Buyurtma tayyor')
    )

    BUYING_TYPE_CHOICES = (
        (BUYING_TYPE_SELF, 'O\'zim olib ketaman'),
        (BUYING_TYPE_DELIVERY, 'Eltuv hizmati')
    )

    customer = models.ForeignKey(Customer, verbose_name='Sotib oluvchi', related_name='related_orders', on_delete=models.CASCADE)
    first_name = models.CharField(max_length=255, verbose_name='Ism')
    last_name = models.CharField(max_length=255, verbose_name='Familiya')
    phone = models.CharField(max_length=20, verbose_name='Telefon raqam')
    cart = models.ForeignKey(Cart, verbose_name='Savatcha', on_delete=models.CASCADE, null=True, blank=True)
    address = models.CharField(max_length=1024, verbose_name='Manzil', null=True, blank=True)
    status = models.CharField(
        max_length=100,
        verbose_name='Buyurtma turi',
        choices=STATUS_CHOICES,
        default=STATUS_NEW
    )
    buying_type = models.CharField(
        max_length=100,
        verbose_name='Buyurtma turi',
        choices=BUYING_TYPE_CHOICES,
        default=BUYING_TYPE_SELF
    )
    comment = models.TextField(verbose_name='Buyurtma haqida fikr bildiring', null=True, blank=True)
    created_at = models.DateTimeField(auto_now=True, verbose_name='Buyurtmani yaratish sanasi')
    order_date = models.DateField(verbose_name='Buyurtmani qabul qilish sanasi', default=timezone.now)

    def __str__(self):
        return str(self.id)


from django.db import models


class Post(models.Model):

    image = models.FileField(blank=True)

class PostImage(models.Model):
    post = models.ForeignKey(Post, default=None, on_delete=models.CASCADE)
    images = models.FileField(upload_to='images/')




