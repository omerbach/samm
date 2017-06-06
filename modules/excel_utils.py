import utils

#taken from http://www.lexicon.net/sjmachin/xlrd.html
XL_CELL_EMPTY = 0	#empty string u''
XL_CELL_TEXT = 1	#a Unicode string
XL_CELL_NUMBER = 2	#float
XL_CELL_DATE = 3	#float
XL_CELL_BOOLEAN = 4	#int; 1 means TRUE, 0 means FALSE
XL_CELL_ERROR = 5	#int representing internal Excel codes; for a text representation, refer to the supplied dictionary error_text_from_code
XL_CELL_BLANK = 6	#empty string u''. Note: this type will appear only when open_workbook(..., formatting_info=True) is used.

def ExtractCellValueByColumn(record, column):
    cell = getattr(record, column, None)
    if cell:
        val = TidyCellValue(cell) 
        
        #if value is textual, strip it        
        if cell.ctype == XL_CELL_TEXT:
            val = cell.value.strip()
        #if value is float, round it to the closest integer        
        elif cell.ctype == XL_CELL_NUMBER:
            val = round(cell.value)
        else:
            val = cell.value
            
        return val
    else:
        return ""    
    
def ExtractCellBackground(cell, sheet):
    try:
        xf = sheet.workSheet.book.xf_list[cell.xf_index]
        bgx = xf.background.pattern_colour_index    
    except AttributeError:
        return -1
    
    return bgx

def TidyCellValue(value):
    
    if isinstance(value, unicode):
        return value.encode('utf-8')
    if isinstance(value, float):
        return str(int(value))
    return str(value)

def ResolveDynamicFieldValue(record, field_name, field_type):
    #print field_name
    field_value = ExtractCellValueByColumn(record, field_name.encode('utf-8'))
    if field_type == 1:
        return field_value
    
    return utils.Intify(field_value)