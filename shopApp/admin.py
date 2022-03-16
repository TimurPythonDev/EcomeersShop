from django.forms import ModelChoiceField,ModelForm
from django.contrib import admin
from .models import *




class SmartphoneAdminForm(ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = kwargs.get('instance')
        if instance and not instance.sd:
            self.fields['sd_volume_max'].widget.attrs.update({
                'readonly': True, 'style': 'background: lightgray;'
            })

    def clean(self):
        if not self.cleaned_data['sd']:
            self.cleaned_data['sd_volume_max'] = None
        return self.cleaned_data






class NotebookAdmin(admin.ModelAdmin):

    def formfield_for_foreignkey(self,db_field,request,**kwargs):
        if db_field.name == 'category':
            return  ModelChoiceField(Category.objects.filter(slug='notebooks'))
        return super().formfield_for_foreignkey(db_field,request,**kwargs)




class SmartphoneAdmin(admin.ModelAdmin):

    def formfield_for_foreignkey(self,db_field,request,**kwargs):
        if db_field.name == 'category':
            return  ModelChoiceField(Category.objects.filter(slug='smartphones'))
        return super().formfield_for_foreignkey(db_field,request,**kwargs)


class PostImageAdmin(admin.StackedInline):
    model = PostImage


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    inlines = [PostImageAdmin]

    class Meta:
        model = Post


@admin.register(PostImage)
class PostImageAdmin(admin.ModelAdmin):
    pass

admin.site.register(Category)
admin.site.register(Notebook,NotebookAdmin)
admin.site.register(Smartphone,SmartphoneAdmin)
admin.site.register(CartProduct)
admin.site.register(Cart)
admin.site.register(Customer)
admin.site.register(Order)

