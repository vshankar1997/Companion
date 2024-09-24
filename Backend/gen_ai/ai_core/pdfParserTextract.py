from textractprettyprinter.t_pretty_print import get_text_from_layout_json
from semantic_text_splitter import MarkdownSplitter
from tokenizers import Tokenizer
from django.conf import settings
from dotenv import load_dotenv
import os
import boto3
import sys
import time
import asyncio  
import json
from ai_core.getChunks import get_doc_chunks_w_metadata
import logging

# Set up logging
logger = logging.getLogger(__name__)

# Get current working directory
cur_path = os.getcwd()
cur_path = cur_path.replace("ai_core", "")

def CreateTopicandQueue(sns, sqs):
    """
    Creates an SNS topic and an SQS queue, and sets up the necessary permissions and subscriptions.

    Args:
        sns (boto3.client): SNS client object
        sqs (boto3.client): SQS client object

    Returns:
        str: SNS topic ARN
        str: SQS queue URL
    """
    millis = str(int(round(time.time() * 1000)))

    # Create SNS topic
    snsTopicName = "AmazonTextractTopic" + millis
    logger.info(f"sns topic name {snsTopicName}")
    topicResponse = sns.create_topic(Name=snsTopicName)
    snsTopicArn = topicResponse['TopicArn']

    # Create SQS queue
    sqsQueueName = "AmazonTextractQueue" + millis
    sqs.create_queue(QueueName=sqsQueueName)
    sqsQueueUrl = sqs.get_queue_url(QueueName=sqsQueueName)['QueueUrl']

    attribs = sqs.get_queue_attributes(QueueUrl=sqsQueueUrl,AttributeNames=['QueueArn'])['Attributes']
    sqsQueueArn = attribs['QueueArn']

    # Subscribe SQS queue to SNS topic
    sns.subscribe(
        TopicArn=snsTopicArn,
        Protocol='sqs',
        Endpoint=sqsQueueArn
    )

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
        QueueUrl=sqsQueueUrl,
        Attributes={
            'Policy': policy
        }
    )
    
    return snsTopicArn, sqsQueueUrl

def GetResults(jobId, textract):
    """
    Retrieves the results of a Textract job.

    Args:
        jobId (str): Textract job ID
        textract (boto3.client): Textract client object

    Returns:
        dict: Textract job results
    """
    maxResults = 1000
    paginationToken = None
    finished = False
    result_value = {}
    while finished == False:
        response = None
        if jobId:
            if paginationToken == None:
                response = textract.get_document_analysis(JobId=jobId, MaxResults=maxResults)
            else:
                response = textract.get_document_analysis(JobId=jobId, MaxResults=maxResults, NextToken=paginationToken)

        logger.info('Detected Document Text')
        logger.info(f"Pages: {response['DocumentMetadata']['Pages']}")
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

async def get_raw_json(s3_bucket_name, doc_name, file_path, textract_client):
    """
    Retrieves the raw JSON output of Textract analysis for a given document.

    Args:
        s3_bucket_name (str): S3 bucket name
        doc_name (str): Document name
        file_path (str): File path
        textract_client (boto3.client): Textract client object

    Returns:
        list: List of document chunks with metadata
    """
    try:
        logger.info(f"starting for - {doc_name}")
        RoleArn = settings.ROLEARN
        sqs = boto3.client('sqs')
        sns = boto3.client('sns')
        snsTopicArn, sqsQueueUrl = CreateTopicandQueue(sns, sqs)
        is_queue_topic_deleted = False
        response = textract_client.start_document_analysis(
            DocumentLocation={'S3Object': {'Bucket': s3_bucket_name, 'Name': file_path + doc_name}},
            FeatureTypes=["LAYOUT", "TABLES"],
            NotificationChannel={'RoleArn': RoleArn, 'SNSTopicArn': snsTopicArn}
        )
        logger.info('Started Analysing Document')
        
        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
            job_id = response['JobId']
            await asyncio.sleep(0.5)
        else:
            sqs.delete_queue(QueueUrl=sqsQueueUrl)
            sns.delete_topic(TopicArn=snsTopicArn)
            is_queue_topic_deleted = True
            logger.info("start analysis failed!")
            
        logger.info(f"{doc_name},  job id: , {job_id}") 

        jobFound = False
        dotLine = 0
        while jobFound == False:
            sqsResponse = sqs.receive_message(QueueUrl=sqsQueueUrl, MessageAttributeNames=['ALL'], MaxNumberOfMessages=10)
            if sqsResponse:
                if 'Messages' not in sqsResponse:
                    if dotLine < 40:
                        dotLine = dotLine + 1
                    else:
                        logger.info('Checking for job completion')
                        dotLine = 0
                    sys.stdout.flush()
                    await asyncio.sleep(0.5)
                    continue
            
                for message in sqsResponse['Messages']:
                    notification = json.loads(message['Body'])
                    textMessage = json.loads(notification['Message'])
                    logger.info(f"Job ID - {textMessage['JobId']}")
                    logger.info(f"Status - {textMessage['Status']}")
                    if str(textMessage['JobId']) == job_id:
                        logger.info(f"Matching Job Found: + {textMessage['JobId']}")
                        jobFound = True
                        raw_json = GetResults(jobId=job_id, textract=textract_client)
                        start_time = time.time()
                        chunks = get_doc_chunks_w_metadata(raw_json, doc_name)
                        # Record the end time
                        end_time = time.time()
                        # Calculate the elapsed time
                        chunking_time = end_time - start_time
                        logger.info(f"Chunking Time: {chunking_time}")
                        sqs.delete_message(QueueUrl=sqsQueueUrl, ReceiptHandle=message['ReceiptHandle'])
                    else:
                        logger.info(f"Job didn't match: {textMessage['JobId']} : {job_id}")
                    # Delete the unknown message. Consider sending to dead letter queue
                    sqs.delete_message(QueueUrl=sqsQueueUrl, ReceiptHandle=message['ReceiptHandle'])
        logger.info('Done!')

        sqs.delete_queue(QueueUrl=sqsQueueUrl)
        sns.delete_topic(TopicArn=snsTopicArn)
        is_queue_topic_deleted = True
        logger.info(f"deleted queue & topic for doc {doc_name}")
        logger.info("__________________________________________________________________________________________________________________")
        
        return chunks
    except Exception as e:
        if not is_queue_topic_deleted:
            sqs.delete_queue(QueueUrl=sqsQueueUrl)
            sns.delete_topic(TopicArn=snsTopicArn)
            is_queue_topic_deleted = True
        logger.info(f"deleted queue & topic for doc {doc_name}")
        logger.info(f"An error occurred: {e}")
        raise(e)

async def process_files(s3_bucket_name, document_names, filepath):
    """
    Processes multiple files asynchronously and returns the combined output and chunks.

    Args:
        s3_bucket_name (str): S3 bucket name
        document_names (list): List of document names
        filepath (str): File path

    Returns:
        tuple: Tuple containing the combined output and chunks
    """
    textract = boto3.client('textract')
    tasks = []
    for doc in document_names:
        task = asyncio.create_task(
            get_raw_json(s3_bucket_name, doc, filepath, textract)
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
