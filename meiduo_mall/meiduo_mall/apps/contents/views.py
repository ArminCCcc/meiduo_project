from django.shortcuts import render
from django.views import View
from collections import OrderedDict

from goods.models import GoodsChannel
from contents.models import Content,ContentCategory
# Create your views here.


class IndexView(View):
    """提供首页广告页面"""
    def get(self,request):
        # 查询并展示商品分类
        # 准备商品分类对应的字典
        categories = OrderedDict()
        # 查询所有的商品频道：37个一级类别
        channels = GoodsChannel.objects.order_by('group_id','sequence')
        # 遍历所有频道
        for channel in channels:
            # 获取当前频道所在的组
            group_id = channel.group_id
            # 构造基本的数据框架：只有11个组
            if group_id not in categories:
                categories[group_id] = {'channels':[],'sub_cats':[]}

            # 查询当前频道的所有一级类别
            cat1 = channel.category
            # 将cat1添加到到对应的一级类别
            categories[group_id]['channels'].append({
                'id':cat1.id,
                'name':cat1.name,
                'url':channel.url
            })

            # 查询二级和三级类别
            for cat2 in cat1.subs.all():  # 从一级类别找二级类别
                cat2.sub_cats = []  # 给二级类别添加一个保存三级类别的列表
                for cat3 in cat2.subs.all():  # 从二级类别找三级类别
                    cat2.sub_cats.append(cat3)  # 将三级类别添加到二级sub_cats

                # 将二级类别添加到一级类别的sub_cats
                categories[group_id]['sub_cats'].append(cat2)

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
