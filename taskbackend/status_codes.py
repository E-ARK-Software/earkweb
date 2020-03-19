status_codes = [
    (0, "Success"),
    (1, "Error"),
    (1019, "Delivery validation failed"),
]

def get_status_code_message(code):
    st_cd_lst = [element[1] for element in status_codes if element[0] == code]
    return "Undefined" if len(st_cd_lst) == 0 else st_cd_lst[0]
