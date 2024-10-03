import csv
import os
from pymongo import MongoClient
from datetime import datetime, timedelta
import pandas as pd


def get_mongodb_client():
    client = MongoClient('mongodb://localhost:27017')
    return client


def get_collection(db, collectn):
    client = get_mongodb_client()
    db = client[db]
    collection = db[collectn]
    return collection, client

def excluded_users():
    return []
    # return ['nabruzzo@amgen.com', 'kguha@amgen.com', 'sgupta24@amgen.com', 'delilahh@amgen.com', 'mmathe01@amgen.com', 'tonyalex@amgen.com','jdasani@amgen.com', 'mswami01@amgen.com', 'ctheveno@amgen.com', 'jwong10@amgen.com', 'gharms@amgen.com', 'npilkent@amgen.com', 'naggar02@amgen.com', 'gkesari@amgen.com', 'apatel27@amgen.com', 'krajulu@amgen.com', 'vshank02@amgen.com', 'dyadav07@amgen.com']

def get_obj_count_for_date():
    try:
        chat_collection, chat_client = get_collection('genai', 'chat_session')
        meta_collection, meta_client = get_collection('genai', 'upload_meta_data')
        payload_list = list()
        skip_emails = excluded_users()
        
        start_date = datetime(2024, 9, 23)
        end_date = datetime.now().replace(hour=23, minute=59, second=59, microsecond=999)
        day_increment = timedelta(days=1)


        # Iterate through dates
        current_date = start_date
        while current_date <= end_date:


            target_date_end = current_date + timedelta(days=1)
            usage_dict = dict()


            #####################################################################################
            result1 = chat_collection.aggregate([
                {
                    '$match': {
                        'created_at': {'$gte': current_date, '$lt': target_date_end}
                    }
                },
                {
                    '$lookup': {
                        'from': 'user_details',
                        'localField': 'user_id',
                        'foreignField': '_id',
                        'as': 'user'
                    }
                },
                {
                    '$match': {
                        'user.email': {'$nin': skip_emails}
                    }
                },
                {
                    '$group': {
                        '_id': '$_id',
                        'count': {'$sum': 1}
                    }
                }
            ])


            result2 = chat_collection.aggregate([
                {
                    '$match': {
                        'created_at': {'$gte': current_date, '$lt': target_date_end}
                    }
                },
                {
                    '$lookup': {
                        'from': 'user_details',
                        'localField': 'user_id',
                        'foreignField': '_id',
                        'as': 'user'
                    }
                },
                {
                    '$match': {
                        'user.email': {'$nin': skip_emails}
                    }
                },
                {
                    '$group': {
                        '_id': '$user_id',
                        'count': {'$sum': 1}
                    }
                }
            ])
            
            result3 = meta_collection.aggregate([
                {
                    '$match': {
                        'created_at': {'$gte': current_date, '$lt': target_date_end}
                    }
                },
                {
                    '$lookup': {
                        'from': 'chat_session',
                        'localField': 'session_id',
                        'foreignField': '_id',
                        'as': 'chat'
                    }
                },
                {
                    '$unwind': '$chat'
                },
                {
                    '$lookup': {
                        'from': 'user_details',
                        'localField': 'chat.user_id',
                        'foreignField': '_id',
                        'as': 'user'
                    }
                },
                {
                    '$unwind': '$user'
                },
                {
                    '$match': {
                        'user.email': {'$nin': skip_emails}
                    }
                },
                {
                    '$group': {
                        '_id': None,
                        'total_length': {'$sum': {'$size': '$files'}}
                    }
                }
            ])


            temp3 = list(result3)
            
            result4 = meta_collection.aggregate([
                {
                    '$match': {
                        'created_at': {'$gte': current_date, '$lt': target_date_end}
                    }
                },
                {
                    '$lookup': {
                        'from': 'chat_session',
                        'localField': 'session_id',
                        'foreignField': '_id',
                        'as': 'chat'
                    }
                },
                {
                    '$unwind': '$chat'
                },
                {
                    '$lookup': {
                        'from': 'user_details',
                        'localField': 'chat.user_id',
                        'foreignField': '_id',
                        'as': 'user'
                    }
                },
                {
                    '$unwind': '$user'
                },
                {
                    '$match': {
                        'user.email': {'$nin': skip_emails}
                    }
                },
                {
                    '$group': {
                        '_id': None,
                        'total_file_size_sum': {'$sum': '$total_file_size'}
                    }
                }
            ])


            temp4 = result4.next()['total_file_size_sum'] if result4.alive else 0
            
            result5 = chat_collection.aggregate([
                {
                    '$match': {
                        'created_at': {'$gte': current_date, '$lt': target_date_end}
                    }
                },
                {
                    '$lookup': {
                        'from': 'user_details',
                        'localField': 'user_id',
                        'foreignField': '_id',
                        'as': 'user_details'
                    }
                },
                {
                    '$unwind': '$user_details'
                },
                {
                    '$match': {
                        'user_details.email': {'$nin': skip_emails}
                    }
                },
                {
                    "$group": {
                        "_id": "$user_id",
                        "email": {"$first": "$user_details.email"}
                    }
                },
                {
                    "$project": {
                        "_id": 1,
                        "email": 1
                    }
                }
            ])


            temp5 = [entry['email'] for entry in result5]
            #####################################################################################
            
            
            usage_dict['Timestamp'] = current_date.strftime("%m-%d-%Y")
            usage_dict['No. of sessions'] = len(list(result1))
            usage_dict['No. of users'] = len(list(result2))
            usage_dict['No. of files uploaded'] = temp3[0]['total_length'] if temp3 else 0
            usage_dict['Total uploaded size (in KB)'] = temp4//1024
            usage_dict['Active users'] = temp5.copy()
            
            payload_list.append(usage_dict.copy())
            current_date += day_increment
        
        chat_client.close()
        meta_client.close()


        return payload_list


    except Exception as e:
        raise Exception(e)


def get_individual_stats():
    chat_collection, chat_client = get_collection('genai', 'chat_session')
    msg_collection, msg_client = get_collection('genai', 'chat_messages')
    user_collection, user_client = get_collection('genai', 'user_details')
    upload_meta_collection, upload_meta_client = get_collection('genai', 'upload_meta_data')
    
    skip_emails = excluded_users()
    usage_dict=dict()
    payload_list=list()
    
    # Following command can be used to get the date range of data
    start_date = datetime(2024, 9, 23)
    end_date = datetime.now().replace(hour=23, minute=59, second=59, microsecond=999)
    
    session_docs_query = {
    "created_at": {"$gte": start_date, "$lte": end_date}
    }
    
    session_docs = chat_collection.find(session_docs_query, {'_id': 1, 'user_id': 1, 'created_at': 1})


    for session in session_docs:
        files = []
        total_file_size = 0
    
        user_email = user_collection.find_one({"_id": session["user_id"]}, {"email": 1,"bu_name": 1})
        if user_email['email'] not in skip_emails:
            timestamp = session['created_at']
            
            positive_rating_count = msg_collection.count_documents({"session_id": session["_id"], "rating": {"$exists": True, "$eq": 1}})


            # Count the occurrences of the "rating" field with value -1
            negative_rating_count = msg_collection.count_documents({"session_id": session["_id"], "rating": {"$exists": True, "$eq": -1}})


            # Count documents in message collection with the same session_id
            message_count = msg_collection.count_documents({"session_id": session["_id"]})
            
            # Count documents in message collection for number of times regenerate happended
            regenerate_count = msg_collection.count_documents({"session_id": session["_id"], "regenerate": {"$exists": True}})


            # Query chat_meta collection to get files and total_file_size based on session_id
            chat_meta_data = upload_meta_collection.find_one({"session_id": session["_id"]}, {"files": 1, "total_file_size": 1})


            # Update files and total_file_size lists
            if chat_meta_data:
                files.extend(chat_meta_data.get("files", []))
                total_file_size += chat_meta_data.get("total_file_size", 0)


            result_time = upload_meta_collection.find_one({"session_id": session["_id"]},{"upload_total_time":1})
            if result_time and "upload_total_time" in result_time:
                upload_total_time = result_time["upload_total_time"]
            else:
                upload_total_time = 0
                
            result_textract_extraction_time = upload_meta_collection.find_one({"session_id": session["_id"]},{"textract_extraction_time":1})
            if result_textract_extraction_time and "textract_extraction_time" in result_textract_extraction_time:
                textract_extraction_time = result_textract_extraction_time["textract_extraction_time"]
            else:
                textract_extraction_time = 0
                
            result_vectorization_time = upload_meta_collection.find_one({"session_id": session["_id"]},{"vectorization_time":1})
            if result_vectorization_time and "vectorization_time" in result_vectorization_time:
                vectorization_time = result_vectorization_time["vectorization_time"]
            else:
                vectorization_time = 0
                
            result_s3_time = upload_meta_collection.find_one({"session_id": session["_id"]},{"s3_upload_time":1})
            if result_s3_time and "s3_upload_time" in result_s3_time:
                s3_time = result_s3_time["s3_upload_time"]
            else:
                s3_time = 0
                
            ai_core_result_time = upload_meta_collection.find_one({"session_id": session["_id"]},{"gen_ai_total_time":1})
            if ai_core_result_time and "gen_ai_total_time" in ai_core_result_time:
                ai_core_time = ai_core_result_time["gen_ai_total_time"]
            else:
                ai_core_time = 0

            usage_dict['Timestamp'] = timestamp.strftime("%m-%d-%Y %H:%M:%S")
            usage_dict['Session ID'] = session['_id']
            usage_dict['Email'] = user_email['email']
            usage_dict['BU'] = user_email['bu_name']
            usage_dict['Prompt Count'] = message_count
            usage_dict['Positive Feedback'] = positive_rating_count
            usage_dict['Negative Feedback'] = negative_rating_count
            usage_dict['Regenerate Count'] = regenerate_count
            usage_dict['Files'] = files
            usage_dict['Total uploaded size (in KB)'] = total_file_size//1024
            usage_dict['Total uploaded time (in sec)'] = upload_total_time
            usage_dict['Total textract time (in sec)'] = textract_extraction_time
            usage_dict['Total vectoriztion time (in sec)'] = vectorization_time
            usage_dict['Total S3 upload time (in sec)'] = s3_time
            usage_dict['Total ai_core time (in sec)'] = ai_core_time
            
            payload_list.append(usage_dict.copy())


    # Close the MongoDB connection
    chat_client.close()
    msg_client.close()
    user_client.close()
    upload_meta_client.close()
    return payload_list


def get_activity_log_data():
    try:
        chat_collection, chat_client = get_collection('genai', 'chat_session')
        msg_collection, msg_client = get_collection('genai', 'chat_messages')
        user_collection, msg_client = get_collection('genai', 'user_details')
        skip_emails = excluded_users()
        payload_list = list()
        start_date = datetime(2024, 9, 23)
        end_date = datetime.now().replace(hour=23, minute=59, second=59, microsecond=999)
        day_increment = timedelta(days=1)


        # Iterate through dates
        current_date = start_date
        while current_date <= end_date:
            target_date_end = current_date + timedelta(days=1)
            activity_dict=dict()
            # Find documents for _id (Sessions)
            result = chat_collection.aggregate([
                {
                    '$match': {
                        'created_at': {'$gte': current_date, '$lt': target_date_end}
                    }
                },
                {
                    '$project': {
                    'session_id': 1,
                    'user_id': 1
                    }
                }
            ])
            
            for document in result:
                chat_obj = msg_collection.find({ "session_id": document["_id"] })
                user_doc = user_collection.find_one({ "_id": document["user_id"] })
                if user_doc.get('email') not in skip_emails:
                    for chat in chat_obj:
                        activity_dict["Datetime"] = chat["created_at"].strftime("%m-%d-%Y %H:%M:%S")
                        activity_dict["Session ID"] = document["_id"]
                        activity_dict["User"] = user_doc.get('email') if user_doc else None
                        activity_dict["BU"] = user_doc.get('bu_name') if user_doc else None
                        activity_dict["Chat ID"] = chat["_id"]
                        activity_dict["Prompt"] = chat["prompt"]
                        activity_dict["Response"] = chat["message"]
                        activity_dict["Regenerate"] = "Yes" if chat.get("regenerate") else "No"
                        activity_dict["Image Included"] = "Yes" if chat.get("image_details") != [] else "No"
                        activity_dict['Response Start Duration (in sec)'] = chat.get('llm_call_time') if chat.get('llm_call_time') else 0
                        activity_dict['Response Streaming Duration (in sec)'] = chat.get('streaming_response_time') if chat.get('streaming_response_time') else 0
                        activity_dict["Feedback"] = "Positive" if chat.get('rating') == 1 else "Negative" if chat.get('rating') == -1 else "Neutral" if chat.get('rating') == 0 else "N/A"
                        if 'tag_ratings' in chat:
                            value = chat['tag_ratings']
                            activity_dict["Accuracy"] = "Like" if value.get('accuracy') == 1 else "Dislike" if value.get('accuracy') == -1 else "N/A"
                            activity_dict["Comprehensiveness"] = "Like" if value.get('comprehensiveness') == 1 else "Dislike" if value.get('comprehensiveness') == -1 else "N/A"
                            activity_dict["Relevant"] = "Like" if value.get('relevant') == 1 else "Dislike" if value.get('relevant') == -1 else "N/A"
                        else:
                            activity_dict["Accuracy"] = "N/A"
                            activity_dict["Comprehensiveness"] = "N/A"
                            activity_dict["Relevant"] = "N/A"
                        activity_dict["User Comments"] = chat.get("feedback", "N/A")
                        payload_list.append(activity_dict.copy())
            current_date += day_increment
            
        chat_client.close()
        msg_client.close()
        return payload_list
    except Exception as e:
        raise Exception(e)
    
def get_activity_image_data():
    try:
        chat_collection, chat_client = get_collection('genai', 'chat_session')
        msg_collection, msg_client = get_collection('genai', 'chat_messages')
        payload_list = list()
        start_date = datetime(2024, 9, 23)
        end_date = datetime.now().replace(hour=23, minute=59, second=59, microsecond=999)
        day_increment = timedelta(days=1)

        # Iterate through dates
        current_date = start_date
        while current_date <= end_date:
            target_date_end = current_date + timedelta(days=1)
            # Find documents for _id (Sessions)
            result = chat_collection.aggregate([
                {
                    '$match': {
                        'created_at': {'$gte': current_date, '$lt': target_date_end}
                    }
                }
            ])

            for document in result:
                chat_obj = msg_collection.find({ "session_id": document["_id"] })
                for chat in chat_obj:
                    if "image_details" in chat and chat.get("image_details") != []:
                        i=1
                        for image in chat.get("image_details"):
                            activity_dict=dict()
                            activity_dict["Datetime"] = chat["created_at"].strftime("%m-%d-%Y %H:%M:%S")
                            activity_dict["Session ID"] = document["_id"]
                            activity_dict["Chat ID"] = chat["_id"]
                            activity_dict["Image ID"] = i
                            activity_dict["Source Document"] = image["document_name"]
                            activity_dict["Page No"] = image["page_number"]
                            activity_dict["Image Path"] = image["path"]
                            activity_dict["Rating"] = "Positive" if image.get("rating") == 1 else "Negative" if image.get("rating") == -1 else "Neutral" if image.get("rating") == 0 else "N/A"
                            payload_list.append(activity_dict.copy())
                            i+=1

            current_date += day_increment

        chat_client.close()
        msg_client.close()
        return payload_list

    except Exception as e:
        raise Exception(e)
    

def create_csv(filename, data):
    try:
        current_date = datetime.now().strftime("%m-%d-%Y")
        csv_file_name = f'{filename} {current_date}.csv'


        # Constructing the file path in the current directory
        current_directory = os.getcwd()
        csv_file_path = os.path.join(current_directory, csv_file_name)
        os.makedirs(os.path.dirname(csv_file_path), exist_ok=True)
        # Writing the CSV file
        with open(csv_file_path, 'w', newline='') as file:
            # Extracting field names from the first dictionary
            field_names = data[0].keys()


            # Creating a CSV writer
            writer = csv.DictWriter(file, fieldnames=field_names)


            # Writing header
            writer.writeheader()


            # Writing data
            writer.writerows(data)


        print(f'CSV file "{csv_file_path}" created successfully.')
    except Exception as e:
        raise Exception(e)
    
def merge_csv_to_excel_and_delete():
    try:
        csv_files = [file for file in os.listdir() if file.endswith('.csv')]


        if not csv_files:
            print("No CSV files found in the current directory.")
            return


        current_date = datetime.now().strftime("%m-%d-%Y")
        filename = f'Usage Report Filtered PROD {current_date}.xlsx'
        excel_writer = pd.ExcelWriter(filename, engine='xlsxwriter')
        for csv_file in csv_files:
            try:
                df = pd.read_csv(csv_file)
                df.replace('N/A', 'N/A', inplace=True)
                sheet_name = os.path.splitext(csv_file)[0]


                df.to_excel(excel_writer, sheet_name=sheet_name, index=False, na_rep='N/A')


                os.remove(csv_file)


                print(f"Data from {csv_file} added to {sheet_name} sheet and the CSV file is deleted.")
            except Exception as e:
                print(f"Error processing {csv_file}: {e}")


        excel_writer.close()


        print(f"All CSV files merged into a single Excel file ({filename}).")
    except Exception as e:
        print(f"An error occurred: {e}")


def get_user_list():
    try:
        email_list = [
            "gkesari@amgen.com",
            "jwong10@amgen.com",
            "tonyalex@amgen.com",
            "apatel27@amgen.com",
            "ataborel@amgen.com",
            "nabruzzo@amgen.com",
            "ctheveno@amgen.com",
            "gharms@amgen.com",
            "kguha@amgen.com",
            "mmathe01@amgen.com",
            "mswami01@amgen.com",
            "naggar02@amgen.com",
            "vshank02@amgen.com",
            "delilahh@amgen.com",
            "jdasani@amgen.com",
            "mshuaib@amgen.com",
            "npilkent@amgen.com",
            "sgupta24@amgen.com",
            "dyadav07@amgen.com",
            "psogi@amgen.com"
        ]

        user_collection, msg_client = get_collection('genai', 'user_details')
        # Fetch data from MongoDB
        cursor = user_collection.find({}, {'username': 1, 'email': 1, 'bu_name': 1, 'user_type': 1})
        data = list(cursor)

        # Process data and update user_type
        for record in data:
            if record['email'] in email_list:
                record['user_type'] = 'Companion Team'
            else:
                record['user_type'] = 'Med Affs'

        # Convert to DataFrame
        df = pd.DataFrame(data)

        if '_id' in df.columns:
            df = df.drop(columns=['_id'])

        # Rename columns
        df.rename(columns={
            'username': 'Name',
            'email': 'Email ID',
            'bu_name': 'Business Unit',
            'user_type': 'User'
        }, inplace=True)

        # Export to CSV
        df.to_csv('Application Users.csv', index=False)

        msg_client.close()
        print("Data exported successfully to 'Application Users.csv'")
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__=="__main__":
    data1 = get_activity_log_data()
    create_csv('Activity Logs',data1)
    
    data2 = get_obj_count_for_date()
    create_csv('Usage Details',data2)
    
    data3 = get_individual_stats()
    create_csv('Session Stats',data3)
    
    data4 = get_activity_image_data()
    create_csv('Image Logs', data4)
    
    get_user_list()
    
    merge_csv_to_excel_and_delete()