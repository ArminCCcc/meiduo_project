

def get_breadcrumb(catergory):
    """
    获取面包屑导航
    :param catergory:类别对象:一级，二级，三级
    :return:一级：返回一级；二级：返回一级+二级；三级：返回一级+二级+三级
    """
    breadcrumb = {
        'cat1':'',
        'cat2':'',
        'cat3':''
    }
    if catergory.parent == None:  # 说明category是一级
        breadcrumb['cat1'] = catergory
    elif catergory.subs.count() == 0:  # 说明category是三级
        cat2 = catergory.parent
        breadcrumb['cat1'] = cat2.parent
        breadcrumb['cat2'] = cat2
        breadcrumb['cat3'] = catergory
    else:  # 说明手机catergory是二级
        breadcrumb['cat1'] = catergory.parent
        breadcrumb['cat3'] = catergory

    return breadcrumb

