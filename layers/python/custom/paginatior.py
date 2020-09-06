import math


class RequestPaginator(object):
    DEFAULT_PAGE_SIZE = 3
    DEFAULT_PARAM_NAME = "page"
    
    total_result_count = 0
    page_count = 0
    page_size = DEFAULT_PAGE_SIZE
    param_name = DEFAULT_PARAM_NAME
    request = None
    number_of_pages = 0

    def __init__(
        self, 
        request:str,
        total_result_count:int,
        page_size:int = DEFAULT_PAGE_SIZE,
        param_name:str = DEFAULT_PAGE_SIZE
    ):
        if total_result_count < 0 or page_size <= 0:
            raise Exception("Invalid arguments")
        self.request = request
        self.total_result_count = total_result_count
        self.page_size = page_size
        self.param_name = param_name
        self.total_result_count = total_result_count
        self.number_of_pages = math.ceil(self.total_result_count / self.page_size)

    
    def paginate(self, results: list, page:int) -> dict:
        if page == 0 or page > self.number_of_pages:
            page = 1
        previous_page = page - 1
        next_page = page + 1
        if self.number_of_pages == 0:
            previous_page = next_page = None
        else:
            if page == 1:
                previous_page = None
            if page == self.number_of_pages:
                next_page = None
            if results == None:
                results = []
        
        previous = self.__construct_request__(previous_page)
        next = self.__construct_request__(next_page)
        
        return {
            "count": self.total_result_count,
            "next": next,
            "previous": previous,
            "results": results
        }

        
    def __construct_request__(self, page: int) -> str:
        if page == None:
            return None
        return f"{self.request}?{self.param_name}={page}"
        