from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage


def paginate(objects_list, request, per_page=10):
    paginator = Paginator(objects_list, per_page)
    page_number = request.GET.get('page', 1)

    try:
        page_int = int(page_number)
        if page_int < 1:
            return paginator.page(1)
        page = paginator.page(page_int)
    except (PageNotAnInteger, ValueError, TypeError):
        page = paginator.page(1)
    except EmptyPage:
        page = paginator.page(paginator.num_pages)

    return page