from textractprettyprinter.t_pretty_print import get_text_from_layout_json
from semantic_text_splitter import MarkdownSplitter
from tokenizers import Tokenizer
import re
import spacy
import tiktoken
import logging
logger = logging.getLogger(__name__)

def tiktoken_len(text):
    """
    Tokenize the input text using a specified tokenizer and return the number of tokens.

    :param text: Input text to be tokenized.
    :return: Number of tokens in the tokenized text.
    """
    try:
        # Tokenize the text using the specified tokenizer
        tokenizer = tiktoken.get_encoding('cl100k_base')
        tokens = tokenizer.encode(
            text,
            disallowed_special=()
        )
        return len(tokens)
        
    except Exception as e:
        raise(e)  

def GetTableChunks(response):
        blocks = response['Blocks']
        tables_dict = get_table_csv_results(blocks)
        return tables_dict

def get_rows_columns_map(table_result, blocks_map):
    rows = {}
    Table_Title = ''
    Table_Footer = ''
    for relationship in table_result['Relationships']:
        if relationship['Type'] == 'CHILD':
            for child_id in relationship['Ids']:
                try:
                    cell = blocks_map[child_id]
                    if cell['BlockType'] == 'CELL':
                        row_index = cell['RowIndex']
                        col_index = cell['ColumnIndex']
                        if row_index not in rows:
                            # create new row
                            rows[row_index] = {}

                        # get the text value
                        rows[row_index][col_index] = get_text(cell, blocks_map)
                except KeyError:
                    logger.error(f"Error extracting Table data - {KeyError}:")
                    pass
        elif relationship['Type'] == 'TABLE_TITLE':
            for child_id in relationship['Ids']:
                text_block = blocks_map[child_id]
                Table_Title += get_text(text_block, blocks_map)
                Table_Title += '\n'
                
        elif relationship['Type'] == 'TABLE_FOOTER':
            for child_id in relationship['Ids']:
                text_block = blocks_map[child_id]
                Table_Footer += get_text(text_block, blocks_map)
                Table_Footer += '\n'
        
    return rows, Table_Title, Table_Footer


def get_text(result, blocks_map):
    text = ''
    if 'Relationships' in result:
        for relationship in result['Relationships']:
            if relationship['Type'] == 'CHILD':
                for child_id in relationship['Ids']:
                    try:
                        word = blocks_map[child_id]
                        if word['BlockType'] == 'WORD':
                            text += word['Text'] + ' '
                        if word['BlockType'] == 'SELECTION_ELEMENT':
                            if word['SelectionStatus'] == 'SELECTED':
                                text += 'X '
                    except KeyError:
                        logger.error(f"Error extracting Table data - {KeyError}:")

    return text

def get_table_csv_results(blocks):

    blocks_map = {}
    table_blocks = []
    for block in blocks:
        blocks_map[block['Id']] = block
        if block['BlockType'] == "TABLE":
            table_blocks.append(block)

    if len(table_blocks) <= 0:
        return {}

    doc_tables = {}
    for index, table in enumerate(table_blocks):
        doc_tables[table['Page']] = doc_tables.get(table['Page'], list())
        doc_tables[table['Page']].append(generate_table_csv(table, blocks_map, index + 1))

    return doc_tables

def generate_table_csv(table_result, blocks_map, table_index):
    rows, table_title, table_footer = get_rows_columns_map(table_result, blocks_map)

    table_id = 'Table_' + str(table_index)

    # get cells.
    csv = 'Table: {0}\n\n'.format(table_id)
    if table_title != '':
        csv += '\nTable Title \n'
        csv +=  table_title
        csv += '\n'
    
    for row_index, cols in rows.items():
        for col_index, text in cols.items():
            csv += '{}'.format(text) + ","
        csv += '\n'
    
    if table_footer != '':
        csv += '\n\nTable Footer \n'
        csv +=  table_footer

    csv += '\n\n'
    return csv

def get_document_text(textract_json):
    doc_text = ''
    all_page_dict = {}
    layout = get_text_from_layout_json(textract_json=textract_json, generate_markdown=True, exclude_page_footer=True,
                                            exclude_page_number=True, exclude_figure_text=True, exclude_page_header=True, skip_table=True)
    for i in layout.keys():
        doc_text += layout[i].strip("\n")
        doc_text += "\n"
        all_page_dict[i] = layout[i].strip("\n")

    return doc_text, all_page_dict

def create_chunks(doc_text):    
    tokenizer = Tokenizer.from_pretrained("bert-base-uncased")
    # Optionally can also have the splitter not trim whitespace for you
    splitter = MarkdownSplitter.from_huggingface_tokenizer(tokenizer, trim_chunks=True)
    chunks = splitter.chunks(doc_text, chunk_capacity=(500,1000))
    return chunks

def find_author(filtered_data):
    """
    Find the Author from the filtered input first page data. Take only chunks < 200 and chunks till total chunk size < 400
    Perform NER on chunks and if no Person entity present then map author as Not Available 

    :param filtered_data (list): The input filtered data to search through.
    :return dict: The author that was found or an 'Not Available' if it wasn't found.
    """
    try:
        # Load the English language model in spaCy  
        nlp = spacy.load('en_core_web_sm')  
        result = {}
        authors = ''
        author_count = 0
        total_token_len = 0
        # Iterate through each element in the input list
        for element in filtered_data:
            # looping only if total token count is < 1000 and if # of authors already found < 5
            if total_token_len <= 1000 and author_count<5:
                # Taking elements only if < 200 tokens
                if tiktoken_len(element) < 500:
                    total_token_len += tiktoken_len(element)
                    doc = nlp(element)  
                    # Iterate through each entity in the document and print out the ones that are persons  
                    for ent in doc.ents:  
                        if ent.label_ == 'PERSON':  
                            
                            # Removing special characters
                            text = re.sub(r'[^\w\s\.\',]', '', str(ent.text))

                            # Replace the links with an empty string
                            pattern = r'https?://\S+'
                            text = re.sub(pattern, '', text)

                            # Remove numbers  
                            text = re.sub(r'\d+', '', text)

                            # if # of words are > 3 then removing
                            if len(text.split(" ")) > 3:
                                continue
                            
                            # if same name then removing
                            if text in authors:
                                continue
                            
                            author_count += 1
                            authors += text
                            # creating a comma separated sting 
                            authors += " , "          
            else:
                break

        # removing trailing ,
        authors = authors.strip(" , ")
        if authors != '':
            result['Authors'] = authors
        else:
            result['Authors'] = 'Not Available'
        return result

    except Exception as e:
        raise(e)

def get_doc_chunks_w_metadata(textract_json, document_name):
    logger.info(f"getting chunks for doc, {document_name}")
    all_chunks_w_metadata = []
    # extracting text from json from
    doc_text, all_page_dict = get_document_text(textract_json)

    # splitting text into chunks using semantic splitter  
    chunks = create_chunks(doc_text)

    # extracting tables from json from
    tables = GetTableChunks(textract_json)

    doc_name = document_name.split("/")[-1]
    # adding metadata : page number, chunk_id and doc name to each chunk
    chunk_id = 0
    authors = find_author(chunks[:4])
    for chunk in chunks:
        chunk_id += 1
        d = {}
        d['Text'] = chunk
        d['pdf_name'] = doc_name
        d['chunk_id'] = chunk_id
        d['Authors'] = authors['Authors']

        page_flag = 0
        for page_num, page_text in all_page_dict.items():
            if chunk[:1000] in page_text:
                page_flag = 1
                d['Page'] = page_num
                
        if page_flag == 0 and chunk_id != 1:
            d['Page'] = all_chunks_w_metadata[-1]['Page'] 
            page_flag = 1
        
        elif chunk_id == 1:
            d['Page'] = 1
        
        if d['Page']!=1 and (d['Page'] > all_chunks_w_metadata[-1]['Page']) and (tables.get(d['Page']-1, -1) != -1):
            for page_table in tables[d['Page']-1]:
                chunk_id += 1
                table_d = {}
                table_d['Text'] = page_table
                table_d['pdf_name'] = doc_name
                table_d['chunk_id'] = chunk_id
                table_d['Authors'] = authors['Authors']
                table_d['Page'] = all_chunks_w_metadata[-1]['Page']
                all_chunks_w_metadata.append(table_d)

        all_chunks_w_metadata.append(d)

    # checking if table in last page 
    if tables.get(list(all_page_dict.keys())[-1], -1) != -1:
        for page_table in tables[list(all_page_dict.keys())[-1]]:
            table_d = {}
            chunk_id += 1
            table_d['Text'] = page_table
            table_d['pdf_name'] = doc_name
            table_d['chunk_id'] = chunk_id
            table_d['Page'] = list(all_page_dict.keys())[-1]
            table_d['Authors'] = authors['Authors']
            all_chunks_w_metadata.append(table_d)

    return all_chunks_w_metadata