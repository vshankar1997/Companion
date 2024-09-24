# FAQ Function

def get_faq_structure():
    data = {
    'FAQs':[
        {
            'faq_string':'Uploaded Docs',
            'type':'faq',
            'questions':[
                {
                    'question':'Will documents that I upload be added to the internal corpus of data? Can my colleagues view documents that I upload?',
                    'answer':'Documents uploaded will not automatically be added to the internal corpus of data. As such, your colleagues are not able to access files that you have uploaded to the tool. Documents will be added to the internal corpus after yearly assessment by the owner of the internal database.'
                },
                {
                    'question':'Will my documents be stored within the tool?',
                    'answer':'Your uploaded documents will be stored within the tool upto 90 days.'
                },
                {
                    'question':'What types of files can I upload?',
                    'answer':'You can upload .pdf files for now. Free text notes, .doc, .ppt, .xls, images or any other file type are not yet supported.'
                },
                {
                    'question':'How many documents can I upload?',
                    'answer':'You can upload 5 .pdfs files at one time. Total file size can\'t be larger than 50 MB. This upload size may increase in the future with updates in functionality.'
                }
            ]
        },
        {
            'faq_string':'Internal Corpus of Data',
            'type':'faq',
            'questions':[
                {
                    'question':'How are Companion\'s data collections started?',
                    'answer':'Medical Affairs and Medical Information team members for each BU determine the key documents that Companion should have access to. These documents are combined into a collection.'
                },
                {
                    'question':'How do documents get added to the Companion internal database?',
                    'answer':'Periodically, a team will review the documents within the corpus of data to ensure that they\'re up to date, and to determine if there are any other documents that should be included.'
                },
                {
                    'question':'How do I get a document added to the internal data collection?',
                    'answer':'If you\'d like to add a document to the curated set, please submit a request to the Companion team or your Companion pilot leads.'
                },
                {
                    'question':'How do I know when the internal data collection has been updated?',
                    'answer':'Users will receive an email when the data collection has been updated, or when there have been any major changes to the Companion\'s functionality.'
                },
                {
                    'question':'Can I download full articles or publications from the internal database?',
                    'answer':'Companion will footnote answers with links to sources in internal data collections. You can use the source links to view and download the full text of publications or documents that contribute to an answer. Currently, there is no way to browse documents in the internal data collection.'
                }
            ]
        },
        {
            'faq_string':'External Data Sources',
            'type':'faq',
            'questions':[
                {
                    'question':'What external databases does the tool have access to?',
                    'answer':'Currently Companion has no access to external data sources.'
                },
                {
                    'question':'How do I add an external database?',
                    'answer':'If you\'d like to add an external database, please submit a request to the Companion team, and the team can evaluate feasibility.'
                }
            ]
        },
        {
            'faq_string':'Analyzing Documents & Generations Results',
            'type':'faq',
            'questions':[
                {
                    'question':'How does the tool analyze documents?',
                    'answer':'This tool is based on a Generative AI Large Language Model that is able to process user queries in natural language and intake many data sources to provide an answer.'
                },
                {
                    'question':'Which document sources can the tool analyze?',
                    'answer':'Companion pulls from two main data sources – the assigned internal data collection and any documents uploaded by user.'
                },
                {
                    'question':'Can Companion analyze multiple data sources for any given query?',
                    'answer':'As of now, Companion is only able to analyze either its internal corpus or uploaded documents to generate responses. Additionally, Companion takes into account the last five conversations from the present session to formulate its answers.'
                },
                {
                    'question':'Can tool analyze tables and images within PDF documents?',
                    'answer':'Yes, Companion can process tables and use them to create responses.'
                },
                {
                    'question':'Does the tool analyze user-generated notes?',
                    'answer':'Yes, Companion can analyze user-generated notes if they\'re uploaded in PDF format.'
                },
                {
                    'question':'How do I switch between data collections?',
                    'answer':'For now, each user is assigned to use one data collection based on their area of expertise. If you\'d like to switch to a different data collection, please contact the Companion team or your Companion pilot leads.'
                }
            ]
        },
        {
            'faq_string':'Exporting & Sharing Results',
            'type':'faq',
            'questions':[
                {
                    'question':'In what formats is the Companion able to produce its outputs? Can Companion generate images with its results?',
                    'answer':'This tool is currently able to produce its outputs in text format along with source details and link to document. In the future, the tool may be able to generate images with its responses.'
                },
                {
                    'question':'In what templates is the tool able to produce its results (i.e. standard response letter, literature review, etc.)?',
                    'answer':'The tool is not currently able to produce results in any pre-defined templates. In the future, it will be included in its functionality.'
                },
                {
                    'question':'How do I add a template format to the tool?',
                    'answer':'If you\'d like to suggest a template format, please submit a request to the Companion team or your Companion pilot leads.'
                },
                {
                    'question':'How do I export my results to another application?',
                    'answer':'You can copy and paste responses for your use in another application. Currently, Companion is not able to export directly into other applications.'
                }
            ]
        },
        {
            'faq_string':'Querying',
            'type':'faq',
            'questions':[
                
                {
                    'question':'How do I find more specific pieces of information within documents?',
                    'answer':'Simply ask Companion a question in natural language in order to find specific pieces of information in documents.'
                },
                {
                    'question':'How can I query the internal data collection when I have also uploaded a document?',
                    'answer':'User must include the phrase \'- refer to internal documents\' in their query in order to access the internal data collection.'
                },
                {
                    'question':'Does tool refer to chat history to answer queries?',
                    'answer':'Yes, Companion considers up to the last five conversations from the present session to formulate answers.'
                },
                {
                    'question':'Will Companion ever generate responses without any sources?',
                    'answer':'Yes, this is possible in some specific scenarios - \n1. When Companion is asked to edit or rewrite a previous response; \n2. When using the \'Regenerate\' button; \n3. When responses are generated only from the previous chat discussion. '
                },
                {
                    'question':'Can I use document name to query?',
                    'answer':'Yes, you can summarize using uploaded document names. For example, Give me summary of "your_uploaded_document.pdf"'
                },
                {
                    'question':'Is Companion restricted from answering any questions?',
                    'answer':'Yes, there may be instances where a response cannot be generated – \n1. Out of context questions.\n2. Due to Azure OpenAI\'s content management policy.'
                },
                {
                    'question':'Am I able to view my past queries?',
                    'answer':'Yes, you can view past 30 days chat sessions in the sidebar.'
                }
            ]
        }
        ]
        }
    
    return data