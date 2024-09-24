import logging
import os.path
import json
import tiktoken
import re
import tempfile
import zipfile
import spacy

logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))

def filter_elements(elements):
    """
    Filter out and keep only the 'Path', 'Text', and 'Page' information for specific element paths.
    Exclude '/Figure', '/Table', '/Footnote', '/StyleSpan', '/Sub', or '/Aside' paths.
    
    :param elements: Dictionary containing the extracted JSON data.
    :return: List of filtered elements with only 'Path', 'Text', and 'Page' information.
    """
    try:
        # Initialize an empty list to store the filtered elements
        filtered_elements = []

        # Iterate through each element in the input list
        for element in elements:
            # Extract the 'Path' from the current element
            path = element.get("Path", "")

            # Skip elements that contain '/Figure', '/Table', '/Footnote', '/StyleSpan', '/Sub', or '/Aside' in their path
            if "/Figure" in path or "/Table" in path or "/Footnote" in path or "/StyleSpan" in path or "/Sub" in path or "/Aside" in path :
                continue

            # Add the filtered element to the result with the page number incremented by 1
            filtered_element = {
                "Path": path,
                "Text": element.get("Text", ""),
                "Page": element.get("Page", None) + 1  # Increment page number by 1
            }
            filtered_elements.append(filtered_element)

        # Return the list of filtered elements
        return filtered_elements
    
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        return None  

def extract_table_prefix(path):
    """
    Extract the prefix of the table path.

    :param path: Table path.
    :return: Table prefix or None if no match is found.
    """
    try:
        # Use a regular expression to search for a specific pattern in the table path
        match = re.search(r'(/Table.*?/|/Aside.*?/)', path)

        # If a match is found, return the matched group (table prefix), otherwise return None
        if match:
            return match.group()
        else:
            return None
            
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        return None  

def filter_and_combine_tables(elements):
    """
    Filter and combine elements based on the 'Path' containing "/Table," "/Aside,"  array.
    Check if the number of words is greater than the number of numbers in the grouped text.
    
    :param elements: List of elements containing various information.
    :return: List of filtered and combined elements meeting the specified condition.
    """
    try:
        # Initialize dictionaries to store grouped tables and filtered elements
        grouped_tables = {}
        filtered_elements = []

        # Iterate through each element in the input list
        for element in elements:
            path = element.get("Path", "")
            
            # Check if the path contains "/Table," "/Aside,"
            if any(keyword in path for keyword in ["/Table", "/Aside"]):
                
                # Check if "Text" is present in the element
                text = element.get("Text")
                if text is not None:
                    # Extract the prefix of the table path
                    path_prefix = extract_table_prefix(path)
                    
                    # Check if the modified path is in the dictionary of grouped tables
                    if path_prefix not in grouped_tables:
                        grouped_tables[path_prefix] = {"Text": "", "Page": set()}

                    # Combine 'Text' and 'Page' for the same path
                    grouped_tables[path_prefix]["Text"] += text + ' '
                    grouped_tables[path_prefix]["Page"].add(element.get("Page", 0) + 1)

        # Convert the grouped_tables dictionary to a list of elements
        combined_elements = [{"Path_Prefix": path, "Text": data["Text"].strip(), "Page": sorted(list(data["Page"]))} for path, data in grouped_tables.items()]

        # Apply additional filtering based on word and number counts
        for element in combined_elements:
            word_count = len(re.findall(r'\b\w+\b', element["Text"]))
            number_count = len(re.findall(r'\b\d+\b', element["Text"]))

            # Check if the number of words is greater than the number of numbers
            if word_count > number_count:
                filtered_element = {
                    "Path_Prefix": element["Path_Prefix"],
                    "Text": element["Text"],
                    "Page": element["Page"],
                }
                filtered_elements.append(filtered_element)

        # Return the list of filtered elements
        return filtered_elements
    
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        return None  

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
        logging.error(f"An error occurred: {e}")
        return None  

def ends_with_full_stop(text):
    """
    Check if a sentence ends with a full stop.
    
    :param text: The text to check.
    :return: True if the text ends with a full stop, False otherwise.
    """
    try:
        # Remove leading and trailing whitespaces
        cleaned_text = text.strip()
        # Check if the last character is a full stop
        return cleaned_text.endswith('.')
        
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        return None  

def merge_pages(input):
    """
    Merge a list of texts and associated pages for min_output_elements, ensuring pages are not added twice.

    :param input: Dictionary containing 'Text' and 'Page' keys with corresponding lists.
    :return: Merged dictionary with combined 'Text' and 'Page' lists.
    """
    try:
        # Create a dictionary with two keys: Text and Page
        output = {'Text': [], 'Page': []}

        # Keep track of pages we've already seen so we don't add them twice
        seen_pages = set()

        # Iterate over input
        for idx, text in enumerate(input['Text']):
            # If this is the first text, add it to output
            if idx == 0:
                output['Text'] = text
                output['Page'] = [page for page in input['Page'][idx] if page not in seen_pages]
                seen_pages.update(input['Page'][idx])
            # If this isn't the first text, add it to the existing text
            else:
                output['Text'] += text
                unique_pages = [page for page in input['Page'][idx] if page not in seen_pages]
                output['Page'] += unique_pages
                seen_pages.update(unique_pages)

        return output
        
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        return None  

def combine_text_and_page(elements, max_token_limit=1000, min_output_tokens=50):
    """
    Combine text and page information.
    
    :param elements: List of elements containing text and page info.
    :param max_token_limit: Maximum token limit for combined text.
    :param min_output_tokens: Minimum number of tokens for the final output text.
    :return: List of combined elements with text and page info.
    """
    try:
        combined_elements = []
        current_combined_text = ""
        current_page = None
        page_numbers = set()
        combined_min_output_elements = {"Text": [], "Page": []}  # Initialize as a dictionary

        for i, element in enumerate(elements):
            path_contains_h1 = "/H1" in element["Path"]
            path_contains_h2 = "/H2" in element["Path"]
            next_chunk_contains_h1 = i < len(elements) - 1 and "/H1" in elements[i + 1]["Path"]

            # Check if adding the next element would exceed the token limit
            # and if there is no full stop, or if H1 is in the next chunk
            if (current_page is None
                or path_contains_h1
                or tiktoken_len(current_combined_text) + tiktoken_len(element["Text"]) <= max_token_limit
                and (ends_with_full_stop(current_combined_text) or next_chunk_contains_h1)):

                # If H1 is in the current path, append the current text and page numbers to the list
                # and reset the current text and page numbers
                if path_contains_h1:
                    if current_combined_text:
                        # Use the list of page numbers if it's not empty, otherwise use the value of 'current_page'
                        page_list = list(page_numbers) if page_numbers else [current_page]
                        # Check if the current text meets the minimum output tokens requirement
                        if tiktoken_len(current_combined_text) >= min_output_tokens:
                            # Add the current text and page list to the combined elements
                            combined_elements.append({"Text": current_combined_text, "Page": page_list})
                        else:
                            # Add the current text and page list to the combined minimum output elements
                            combined_min_output_elements["Text"].append(current_combined_text)
                            combined_min_output_elements["Page"].append(page_list)
                        current_combined_text = ""
                        page_numbers.clear()

                # Add the element text to the current text and update the page numbers
                if path_contains_h1:
                    current_combined_text += element["Text"] +'\n \n '
                elif not ends_with_full_stop(element["Text"]) and not path_contains_h2:
                    current_combined_text += element["Text"]
                else:
                    current_combined_text += element["Text"] + '\n '
                page_numbers.add(element["Page"])

            else:
                # If the text does not end with a full stop and the next path is not H1
                # add the element text to the current text and update the page numbers
                if not ends_with_full_stop(current_combined_text) and not next_chunk_contains_h1:
                    if ends_with_full_stop(element["Text"]) or path_contains_h2:
                        current_combined_text += element["Text"] +'\n '
                    else:
                        current_combined_text += element["Text"]
                    page_numbers.add(element["Page"])
                else:
                    # Use the list of page numbers if it's not empty, otherwise use the value of 'current_page'
                    page_list = list(page_numbers) if page_numbers else [current_page]
                    # Check if the current text meets the minimum output tokens requirement
                    if tiktoken_len(current_combined_text) >= min_output_tokens:
                        # Add the current text and page list to the combined elements
                        combined_elements.append({"Text": current_combined_text, "Page": page_list})
                    else:
                        # Add the current text and page list to the combined minimum output elements
                        combined_min_output_elements["Text"].append(current_combined_text)
                        combined_min_output_elements["Page"].append(page_list)
                    current_combined_text = ""
                    page_numbers.clear()
                    # Otherwise, append the current text and page numbers to the list
                    # and set the current text to the element text and reset the page numbers
                    if ends_with_full_stop(element["Text"]) or path_contains_h2:
                        current_combined_text += element["Text"] + '\n '
                        page_numbers.add(element["Page"])
                    else:
                        current_combined_text += element["Text"]
                        page_numbers.add(element["Page"])


            # Set the current page to the element page
            current_page = element["Page"]

        # Append the last text and page numbers to the list if any
        if current_combined_text:
            if tiktoken_len(current_combined_text) >= min_output_tokens:
                combined_elements.append({"Text": current_combined_text, "Page": list(page_numbers)})
            else:
                combined_min_output_elements["Text"].append(current_combined_text)
                combined_min_output_elements["Page"].append(list(page_numbers))
    

        return  ([merge_pages(combined_min_output_elements)] if combined_min_output_elements["Text"] else []) + combined_elements
        
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        return None  

def find_title(input_data, paths_to_find):
    """
    Find the title from the list of paths to find. If the path isn't found, the
    title is set to an empty string.

    :param input_data (list): The input data to search through.
    :param paths_to_find (list): The list of paths to find.
    :return dict: The title that was found or an empty string if it wasn't found.
    """
    try:
        result = {}
        for path_filter in paths_to_find:
            for entry in input_data:
                if entry.get('Path', '') == path_filter:
                    result['Title'] = entry.get('Text', '')
                    break
                else:
                    result['Title'] = 'Not Available'
        return result
        
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        return None  

def filter_elements_author(elements):
    """
    Filter out and keep only the 'Path', 'Text', and 'Page' information for specific element paths.
    Exclude '/Figure', '/Table', '/Footnote', '/StyleSpan', '/Title' paths and elements of page > 0.
    
    :param elements: Dictionary containing the extracted JSON data.
    :return: List of filtered elements with only 'Path', 'Text', and 'Page' information.
    """
    try:
        # Initialize an empty list to store the filtered elements
        filtered_elements = []

        # Iterate through each element in the input list
        for element in elements:
            # Extract the 'Path' from the current element
            path = element.get("Path", "")

            # Skip elements that contain '/Figure', '/Table', '/Footnote', '/StyleSpan', '/Title', or if page number is > 0
            if "/Figure" in path or "/Table" in path or "/Footnote" in path or "/StyleSpan" in path or "/Title" in path or element["Page"] > 0 :
                continue

            # Add the filtered element to the result with the page number incremented by 1
            filtered_element = {
                "Path": path,
                "Text": element.get("Text", ""),
                "Page": element.get("Page", None) + 1  # Increment page number by 1
            }
            filtered_elements.append(filtered_element)

        # Return the list of filtered elements
        return filtered_elements
    
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        return None  


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
            # looping only if total token count is < 400 and if # of authors already found < 5
            if total_token_len <= 400 and author_count<5:
                # Taking elements only if < 200 tokens
                if tiktoken_len(element["Text"]) < 200:
                    total_token_len += tiktoken_len(element["Text"])
                    doc = nlp(element["Text"])  
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
        logging.error(f"An error occurred: {e}")
        return None  

def process_pdf(result_json, pdf_name):

    try:

        # extracting text annd converting pdf to json using Adobe Extract API

        # Filtering required data
        filtered_elements = filter_elements(result_json.get("elements", []))

        # Filtering data for finding Authors
        filtered_first_page_ele = filter_elements_author(result_json.get("elements", []))

        # Extracting Authors of the PDF
        author_found = find_author(filtered_first_page_ele)

        # Filter and group table information based on content
        filtered_and_combined_tables = filter_and_combine_tables(result_json.get("elements", []))
        
        # Cleaning and creating relevant chunks
        filtered_and_combined_para = combine_text_and_page(filtered_elements)

        # Combine filtered para and table data. Drop 'Path_Prefix' key from the result
        final_elements = filtered_and_combined_para + [{"Text": element["Text"] + ' \n ', "Page": element["Page"]} for element in filtered_and_combined_tables]

        # Extracting Title of the PDF
        title_found = find_title(result_json.get("elements", []), ['//Document/Title'])

        # Assuming pdf_name_dict is defined somewhere
        pdf_name_dict = {"pdf_name": pdf_name}

        # Add title_found, author_found and pdf_name_dict to each element in final_elements
        final_elements_with_metadata = [{**element, **title_found, **pdf_name_dict, **author_found} for element in final_elements]

        # Remove 'Page' as list into a string
        pdf_parser_output = [{'Text': item['Text'],
            'Page': ', '.join(map(str, item['Page'])),
            'Title': item['Title'],
            'pdf_name': item['pdf_name'],
            'Authors': item['Authors']} for item in final_elements_with_metadata]

        return pdf_parser_output
        
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        return None