from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer, LTChar
import re
import json
import boto3
import json

# initializing s3 connection with boto client

session = boto3.Session(
    aws_access_key_id='AKIA5YZNISARGR7EVXW5',
    aws_secret_access_key='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',
    region_name='ap-south-1',
)

# Creating S3 Resource From the Session.

client = session.client('s3')


text_list = []
text_size = []

def find_between_r( s, first, last ):
    try:
        start = s.rindex( first ) + len( first )
        end = s.rindex( last, start )
        return s[start:end]
    except ValueError:
        return ""

def containsLetterAndNumber(input):
    has_letter = False
    has_number = False
    for x in input:
        if x.isalpha():
            has_letter = True
        elif x.isnumeric():
            has_number = True
        if has_letter or has_number:
            return True
    return False


def json_resume(event, context):
    s3 = boto3.client("s3")
    bucket_name = 'my-pdf-upload-bucket'
    if event:
        file_obj = event["Records"][0]
        filename = str(file_obj["s3"]["object"]["key"])
        print(filename)
        if filename.split('.')[-1] == 'pdf':
            tmp_filename = '/tmp/' + str(filename)
            print(tmp_filename)
            s3.download_file(bucket_name, filename, tmp_filename)
            for page_layout in extract_pages(tmp_filename):
                for element in page_layout:
                    if isinstance(element, LTTextContainer):
                        temp_text = element.get_text()
                        if(containsLetterAndNumber(temp_text)):
                            text_list.append(element.get_text())
                            for text_line in element:
                                for character in text_line:
                                    if isinstance(character, LTChar):
                                        text_size.append(character.size)
                                        break
                                break
            name = ''
            skills = []
            contact_number = 0
            linkedin_url = ''
            job_role = '' 
            current_location = ''
            email = ''
            summary = ''
            experience = []
            education = []
            for idx, val in enumerate(text_size):
                if(int(text_size[idx]) == 26):
                    name = text_list[idx].replace("\n", "")
                    job_role = text_list[idx+1].split("\n")[0]
                    current_location = text_list[idx+1].split("\n")[1]
                if(text_list[idx]=='Summary\n'):
                    count = idx+1
                    while(text_size[idx+1] == text_size[count]):
                        summary= summary + text_list[count].replace("\n",'')
                        count = count+1
                if(text_list[idx]=='Experience\n' and text_size[idx] == 15.75):
                    count = idx+1
                    while(text_size[idx] > text_size[count] and len(text_list)-1 > count):
                        temp_exp = text_list[count]
                        count = count+1
                        while(text_size[count] < 11 and len(text_list) > count):
                            temp_exp = temp_exp + text_list[count]
                            count = count+1
                            experience.append(temp_exp)
                if(text_list[idx]=='Education\n' and text_size[idx] == 15.75):
                    count = idx+1
                    while(text_size[idx] > text_size[count] and len(text_list)-1 > count):
                        temp_edu = text_list[count]
                        count = count+1
                        while(len(text_list)-1 > count and text_size[count] < 11):
                            temp_edu = temp_edu + text_list[count]
                            count = count+1
                        education.append(temp_edu)
                if(text_list[idx]=='Contact\n'):
                    contact_number = re.sub('\D', '', text_list[idx+1])
                    email = text_list[idx+1].split('\n')[1]
                if(text_list[idx] == 'Top Skills\n'):
                    skills.append(text_list[idx+1].replace("\n", ""))
                    skills.append(text_list[idx+2].replace("\n", ""))
                    skills.append(text_list[idx+3].replace("\n", ""))
                if(text_list[idx].find("linkedin.com")!=-1):
                    # extracting the linked in url of a profile
                    unprocessed_linkedin = find_between_r(text_list[idx], "www.linkedin.com", "(LinkedIn)" )
                    linkedin_url = 'https://www.linkedin.com'+unprocessed_linkedin.replace("\n", "")
            
            data = {
                "linkedin_url":linkedin_url,
                "name":name,
                "email":email,
                "contact_number":contact_number,
                "current_location":current_location,
                "job_role":job_role,
                "summary":summary,
                "skills":skills,
                "experience":experience,
                "eduction":education
            }

            data = json.dumps(data).encode('UTF-8')

            json_file = filename.split('.')[-2]
            json_file = json_file+'.json'
            result = client.put_object(ACL='public-read',Body=data, Bucket='my-pdf-upload-bucket', Key=json_file)

            res = result.get('ResponseMetadata')

            # To generate cloudwatch logs
            if res.get('HTTPStatusCode') == 200:
                print('File Uploaded Successfully')
            else:
                print('File Not Uploaded')
            

