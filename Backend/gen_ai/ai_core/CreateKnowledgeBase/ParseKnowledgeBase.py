from textractprettyprinter.t_pretty_print import get_text_from_layout_json
from semantic_text_splitter import MarkdownSplitter
from tokenizers import Tokenizer
from dotenv import load_dotenv
import os
import boto3
import sys
import time
import asyncio  
import json
import pickle
import re
from KnowledgeBaseChunking import get_doc_chunks_w_metadata

cur_path=os.getcwd()
cur_path=cur_path.replace("ai_core/CreateKnowledgeBase", "")

# document_names = ['Slentz_Teprotumumab a novel therapeutic monoclonal antibody to thyroid-assocaited ophthalmopathy.pdf', 'Kang_Infusion Center Guidelines for Teprotumumab Infusions - Informed Consent Safety during Pandemic and Management of Side Effe.pdf', 'Douglas_Proptosis and diplopia response in moderate-to-severe thyroid eye disease a matching-adjusted indirect comparison of tep.pdf']
# document_names = ['Douglas_Proptosis and diplopia response in moderate-to-severe thyroid eye disease a matching-adjusted indirect comparison of tep.pdf']

def list_pdf_files(bucket_name, prefix, s3_client):
    """
    Lists all PDF files in the specified S3 bucket under the given prefix.
    Args:
        bucket_name (str): Name of the S3 bucket.
        prefix (str): Prefix (folder path) within the bucket.

    Returns:
        list: List of PDF file names.
    """
    response = s3_client.list_objects_v2(
        Bucket=bucket_name,
        Prefix='KNOWLEDGEBASE/'+prefix)

    pdf_files = [content['Key'].split("/")[-1] for content in response.get('Contents', []) if content['Key'].lower().endswith('.pdf')]
    return pdf_files

def GetResults(jobId, textract):
    maxResults = 1000
    paginationToken = None
    finished = False
    result_value = {}
    while finished == False:
        response = None
        if jobId:
            if paginationToken == None:
                response = textract.get_document_analysis(JobId=jobId,
                                                                MaxResults=maxResults)
            else:
                response = textract.get_document_analysis(JobId=jobId,
                                                                MaxResults=maxResults,
                                                                NextToken=paginationToken)

        print('Detected Document Text')
        print('Pages: {}'.format(response['DocumentMetadata']['Pages']))
        print()
        if "Blocks" in result_value:
            result_value["Blocks"].extend(response["Blocks"])
        else:
            result_value = response
        if "NextToken" in response:
            paginationToken = response['NextToken']
        else:
            finished = True  
    if "NextToken" in result_value:
        del result_value["NextToken"]

    return result_value

def CreateTopicandQueue(sns, sqs):

    millis = str(int(round(time.time() * 1000)))

    # Create SNS topic
    snsTopicName = "AmazonTextractTopic" + millis
    print("sns topic name", snsTopicName)
    topicResponse = sns.create_topic(Name=snsTopicName)
    snsTopicArn = topicResponse['TopicArn']

    # create SQS queue
    sqsQueueName = "AmazonTextractQueue" + millis
    sqs.create_queue(QueueName=sqsQueueName)
    sqsQueueUrl = sqs.get_queue_url(QueueName=sqsQueueName)['QueueUrl']

    attribs = sqs.get_queue_attributes(QueueUrl=sqsQueueUrl,AttributeNames=['QueueArn'])['Attributes']

    sqsQueueArn = attribs['QueueArn']

    # Subscribe SQS queue to SNS topic
    sns.subscribe(
        TopicArn=snsTopicArn,
        Protocol='sqs',
        Endpoint=sqsQueueArn)

    # Authorize SNS to write SQS queue
    policy = """{{
    "Version":"2012-10-17",
    "Statement":[
        {{
        "Sid":"MyPolicy",
        "Effect":"Allow",
        "Principal" : {{"AWS" : "*"}},
        "Action":"SQS:SendMessage",
        "Resource": "{}",
        "Condition":{{
            "ArnEquals":{{
            "aws:SourceArn": "{}"
            }}
        }}
        }}
    ]
    }}""".format(sqsQueueArn, snsTopicArn)

    response = sqs.set_queue_attributes(
        QueueUrl= sqsQueueUrl,
        Attributes={
            'Policy': policy
        })
    
    return snsTopicArn, sqsQueueUrl

async def get_raw_json(s3_bucket_name, doc_name, file_path, doc_metadata, textract_client):
    try :
        print("starting for - ", doc_name)
        RoleArn = os.environ["ROLEARN"]
        sqs = boto3.client('sqs')
        sns = boto3.client('sns')
        snsTopicArn, sqsQueueUrl = CreateTopicandQueue(sns, sqs)
        is_queue_topic_deleted = False
        response = textract_client.start_document_analysis(DocumentLocation={'S3Object': {'Bucket': s3_bucket_name, 'Name': file_path+doc_name}}, FeatureTypes=["LAYOUT","TABLES"],
                                                        NotificationChannel={'RoleArn': RoleArn, 'SNSTopicArn': snsTopicArn})
        print('Processing type: Analysis')
        
        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
            job_id = response['JobId']
            await asyncio.sleep(0.5)
        else:
            sqs.delete_queue(QueueUrl=sqsQueueUrl)
            sns.delete_topic(TopicArn=snsTopicArn)
            is_queue_topic_deleted = True
            print("start analysis failed!")
            
        print(doc_name, " job id: ", job_id)    

        queue_url = sqsQueueUrl
        jobFound = False
        dotLine = 0
        while jobFound == False:
            sqsResponse = sqs.receive_message(QueueUrl=queue_url, MessageAttributeNames=['ALL'],
                                                    MaxNumberOfMessages=10, WaitTimeSeconds=2)
            if sqsResponse:
                if 'Messages' not in sqsResponse:
                    if dotLine < 40:
                        print('.', end='')
                        dotLine = dotLine + 1
                    else:
                        print()
                        dotLine = 0
                    sys.stdout.flush()
                    await asyncio.sleep(0.5)
                    continue
            
                for message in sqsResponse['Messages']:
                    notification = json.loads(message['Body'])
                    textMessage = json.loads(notification['Message'])
                    print(textMessage['JobId'])
                    print(textMessage['Status'])
                    if str(textMessage['JobId']) == job_id:
                        print('Matching Job Found:' + textMessage['JobId'])
                        jobFound = True
                        raw_json = GetResults(jobId=job_id, textract=textract_client)
                        try :
                            textract_json = json.dumps(raw_json)
                            # Upload the JSON data to S3
                            folder_name="".join(doc_name.split(".")[:-1])
                            object_key = 'KnowledgeBase_Extracts/'+KnowledgeBaseName+"/"+folder_name+"/"+'Raw_Textract_Output.json'
                            s3.put_object(Bucket=s3_bucket_name, Key=object_key, Body=textract_json)
                            print("for doc, ", doc_name, " json stored")
                        except:
                            print("error in storing json")
                            
                        chunks = get_doc_chunks_w_metadata(raw_json, doc_name, doc_metadata)
                        try:
                            chunk_pkl_obj =pickle.dumps(chunks)
                            object_key = 'KnowledgeBase_Extracts/'+KnowledgeBaseName+"/"+folder_name+"/"+'chunks.pkl'
                            s3.put_object(Bucket=s3_bucket_name, Key=object_key, Body=chunk_pkl_obj)
                            print("for doc, ", doc_name, " chunks stored")
                        except:
                            print("error in storing chunks")
                        sqs.delete_message(QueueUrl=queue_url,ReceiptHandle=message['ReceiptHandle'])
                    else:
                        print("Job didn't match:" +
                                str(textMessage['JobId']) + ' : ' + str(job_id))
                    # Delete the unknown message. Consider sending to dead letter queue
                    sqs.delete_message(QueueUrl=queue_url,ReceiptHandle=message['ReceiptHandle'])
        print('Done!')

        sqs.delete_queue(QueueUrl=sqsQueueUrl)
        sns.delete_topic(TopicArn=snsTopicArn)
        is_queue_topic_deleted = True
        print("deleted queue & topic for doc ", doc_name)
        print("__________________________________________________________________________________________________________________")
        
        return chunks
    except Exception as e:
        if is_queue_topic_deleted == False:
            sqs.delete_queue(QueueUrl=sqsQueueUrl)
            sns.delete_topic(TopicArn=snsTopicArn)
            is_queue_topic_deleted = True
        print("deleted queue & topic for doc ", doc_name)
        print(f"An error occurred: {e}")
        raise(e)

def replace_keys_with_alphanumeric(dict_obj):  
    new_dict = {}  
    for key, value in dict_obj.items():  
        new_key = re.sub(r'[^a-zA-Z0-9]', '', key)  
        new_dict[new_key] = value  
    return new_dict

def read_metadata(bucket_name, KB_Name):
    try:
        file_key="KnowledgeBase_Metadata/"+KB_Name+"_Metadata.json"
        response = s3.get_object(Bucket=bucket_name, Key=file_key)
        file_content = response['Body'].read()
        json_content = json.loads(file_content)
        updated_dict = replace_keys_with_alphanumeric(json_content)
        return updated_dict
    except Exception as e:
        print(f"Error reading the file: {e}")
        raise(e)

async def process_files(s3_bucket_name, filepath):
    pdf_files_list = list_pdf_files(bucket_name=s3_bucket_name, prefix=KnowledgeBaseName, s3_client=s3)
    doc_metadata = read_metadata(s3_bucket_name,KnowledgeBaseName)
    textract = boto3.client('textract')
    tasks = []
    additional_doc_list = ['Kümpfel, T et al. NEMOS dx and treatment recommendations. 2024  Jrl Neurol.pdf']
    # for doc in pdf_files_list:
    for doc in additional_doc_list:    
        task = asyncio.create_task(
            get_raw_json(s3_bucket_name, doc, filepath, doc_metadata, textract)
        )
        tasks.append(task)

    all_pdf_output = await asyncio.gather(*tasks)
    
    all_chunks = []
    for pdf_output in all_pdf_output:
        if all_chunks == []:
            all_chunks = pdf_output
        else:
            all_chunks += pdf_output

    return all_pdf_output, all_chunks

# create an s3 client
s3 = boto3.client('s3')

# name of knowledge base to parse 
# update here
KnowledgeBaseName = "UPLIZNA"

processed_output_, all_chunks = asyncio.run(process_files(os.environ["S3_BUCKET_NAME"], 'KNOWLEDGEBASE/'+KnowledgeBaseName+'/'))