def parse_text_to_txtfile_and_table_to_csvfile():
    
    help_text = '''
    This is a python function that parses text into a txt file 
    and tables into a csv file.
    
    This function requires the following information:
    
    1.document: This is the path to the pdf file you want to
                 extract the text and tables from.
    2.page number:This is the page number in the pdf file above
                 from where you want to extract the text and 
                 table from.
    3.table title:This is a string indicating the start of the
                  table in the requested page. Note: This would
                  be included in the table.
    4.table end:This is a string indicating the end of the
                table in the requested page. Note: This would
                be included in the table.
    5.output txt file name: This is the name of the txt file you want the
                   extracted texts to be saved into.
    6.output csv file: This is the name of the csv file you want the
                   extracted texts to be saved into.
                    
    

    
    ''' 
    print(help_text)
    
    
    document = str(input('Please input the document'))
    print(' ')
    page_number = int(input('Please input the page number'))
    table_title = str(input('Please input the table title')) 
    table_end = str(input('Please input the table end'))
    output_txt_file = str(input('Please input the output txt file name'))
    output_csv_file = str(input('Please input the output csv file name'))

    
    
    #IMPORTING RELEVANT MODULES
    import fitz
    import json
    import sqlite3
    
    
    ###FUNCTION DEFINITIONS
    
        
    
    
    
    
    
    def sorting_page_blocks(blocks):
        '''
        This function sorts the blocks of a TextPage in ascending vertical pixel order,
        then in ascending horizontal pixel order.
        '''
        sorted_blocks = []
        for b in blocks:
            x0 = str(int(b["bbox"][0]+0.99999)).rjust(4,"0") # x coord in pixels
            y0 = str(int(b["bbox"][1]+0.99999)).rjust(4,"0") # y coord in pixels
            sortkey = y0 + x0                                # = "yx"
            sorted_blocks.append([sortkey, b])
        sorted_blocks.sort()
        return [b[1] for b in sorted_blocks]
    
    

    def read_text(blocks,table_title,table_end):
        fout = open(output_txt_file + '.txt',"w")
        pg_text = " "   
        for b in blocks:
            lines = b["lines"]# ... lines
            for l in lines:
                spans = l["spans"]        # ... spans
                for s in spans:
                    
                    #Checks if the current text is the table title to stop parsing the text
                    if s['text'] == table_title:
                        fout.write(pg_text)
                        
                    else:
                        if pg_text.endswith(" ") or s["text"].startswith(" "):
                            pg_text += s["text"]
                        else:
                            pg_text += " " + s["text"]
                            pg_text += "\n"
         
        pg_text= " "
        for i in range(len(blocks)):
            if blocks[i]['lines'][0]['spans'][0]['text'] == table_end:
                j = range(i+1,len(blocks))
                
        
        
        for k in j:
             for s in blocks[k]['lines'][0]['spans']:
                    pg_text += " " + s["text"]
                    pg_text += "\n"
                    
    
        fout.write(pg_text)
        fout.close()
    
    
    
    def read_Table(bbox, columns = None):
        '''
        This function reads a table in a pdf and converts it into a list of list of strings
    
        Parameters:
        bbox: containing rectangle, list of numbers [xmin, ymin, xmax, ymax]
        columns: optional list of column coordinates. If None, columns are generated.

        Returns the parsed table as a list of lists of strings.
        '''
        import json
        import sqlite3
        xmin, ymin, xmax, ymax = bbox                # rectangle coordinates
        if not (xmin < xmax and ymin < ymax):
            return "Warning: incorrect containing rectangle coordinates!"

    
        db = sqlite3.connect(":memory:")        # create RAM database
        cur = db.cursor()
        # create a table for the spans (text pieces)
        cur.execute("CREATE TABLE `spans` (`x0` REAL,`y0` REAL, `text` TEXT)")

    
        def spanout(s, y0):
            x0  = s["bbox"][0]
            txt = s["text"]          # the text piece
            cur.execute("insert into spans values (?,?,?)", (int(x0), int(y0), txt))
            return
    
        
        for block in blocks:
            for line in block["lines"]:
                y0 = line["bbox"][1]            # top-left y-coord
                y1 = line["bbox"][3]            # bottom-right y-coord
                if y0 < ymin or y1 > ymax:      # line outside bbox limits - skip it
                    continue
                spans = []                      # sort spans by their left coord's
                for s in line["spans"]:
                    if s["bbox"][0] >= xmin and s["bbox"][2] <= xmax:
                        spans.append([s["bbox"][0], s])
                if spans:                       # any spans left at all?
                    spans.sort()                # sort them
                else:
                    continue
                # concatenate spans close to each other
                for i, s in enumerate(spans):
                    span = s[1]
                    if i == 0:
                        s0 = span                    # memorize 1st span
                        continue
                    x0  = span["bbox"][0]            # left borger of span
                    x1  = span["bbox"][2]            # right border of span
                    txt = span["text"]               # text of this span
                    if abs(x0 - s0["bbox"][2]) > 3:  # if more than 3 pixels away
                        spanout(s0, y0)              # from previous span, output it
                        s0 = span                    # store this one as new 1st
                        continue
                    s0["text"] += txt                # join current span with prev
                    s0["bbox"][2] = x1               # save new right border
                spanout(s0, y0)                      # output the orphan

        # create a list of all the begin coordinates (used for column indices).

        if columns:                        
            coltab = columns
            coltab.sort()                  
            if coltab[0] > xmin:
                coltab = [xmin] + coltab   
        else:
            cur.execute("select distinct x0 from spans order by x0")
            coltab = [t[0] for t in cur.fetchall()]

        # now read all text pieces from top to bottom.
        cur.execute("select x0, y0, text from spans order by y0")
        alltxt = cur.fetchall()
        db.close()                              

        # create the matrix
        spantab = []

        try:
            y0 = alltxt[0][1]                   # y-coord of first line
        except IndexError:                      # nothing there:
            print("Warning: no text found in rectangle!")
            return []

        zeile = [""] * len(coltab)

        for c in alltxt:
            c_idx = len(coltab) - 1
            while c[0] < coltab[c_idx]:         # col number of the text piece
                c_idx = c_idx - 1
            if y0 < c[1]:                       # new line?
                # output old line
                spantab.append(zeile)
                # create new line skeleton
                y0 = c[1]
                zeile = [""] * len(coltab)
            if not zeile[c_idx] or zeile[c_idx].endswith(" ") or\
                               c[2].startswith(" "):
                zeile[c_idx] += c[2]
            else:
                zeile[c_idx] += " " + c[2]

        # output last line
        spantab.append(zeile)
        return spantab



    #####MAIN PROGRAM
    
    #read in the document file and loading the page using fitz and converting it to a json file 
    document = fitz.open('1-ProVen-VCT-Annual-Report_Accounts_2.pdf')                            
    page = document.loadPage(page_number)                         # load page number i
    text = page.getText('json')           # get its text in JSON format
    pgdict = json.loads(text)
        
    #Searching for thr top and botttom part of the table    
    search1 = page.searchFor(table_title, hit_max = 1)
    if not search1:
        print("warning: table bottom delimiter not found - using beginning of page")
        ymin = 0
    else:    
        rect1 = search1[0]  
        ymin = rect1.y1    
        
    search2 = page.searchFor(table_end , hit_max = 1)
    if not search2:
        print("warning: table bottom delimiter not found - using end of page")
        ymax = 99999
    else:
        rect2 = search2[0]  # the rectangle that surrounds the search string
        ymax = rect2.y1     # table ends above this value

    if not ymin < ymax:     # something was wrong with the search strings
        raise ValueError("table bottom delimiter greater than top")
      
    
    
    blocks = sorting_page_blocks(pgdict["blocks"])
    read_text(blocks,table_title,table_end)
    
        
    tab = read_Table([0, ymin, 9999, ymax])
    csv = open(output_csv_file + '.csv', "w")
    csv.write(table_title + "\n")
    for t in tab:
        csv.write("|".join(t) + "\n")
    csv.close()
    
