from django.shortcuts import render
from django.views import View
from collections import OrderedDict

from contents.models import ContentCategory
from contents.utils import get_categories
# Create your views here.


class IndexView(View):
    """提供首页广告页面"""
    def get(self,request):
        # 查询并展示商品分类
        # 准备商品分类对应的字典
        categories = get_categories()
        # 查询首页广告数据
        # 查询所有的广告类别
        contents = OrderedDict()
        content_categories = ContentCategory.objects.all()
        for content_category in content_categories:
            # 查出未下架的广告并排序
            contents[content_category.key] = content_category.content_set.filter(status=True).order_by('sequence')

        # 构造上下文
        context = {'categories':categories,
                    'contents':contents,
        }
        return render(request,'index.html',context)
