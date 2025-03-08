import streamlit as st
import requests
import boto3
import os
from dotenv import load_dotenv
# Load AWS credentials from .env
load_dotenv()

## for streamlit handling##
###-----------------------------------
# Retrieve AWS credentials from Streamlit secrets
aws_access_key = st.secrets["AWS_ACCESS_KEY_ID"]
aws_secret_key = st.secrets["AWS_SECRET_ACCESS_KEY"]
####-----------------------------------

# API url of the lambda function
API_GATEWAY_URL = "https://8p3sqp34i1.execute-api.us-east-1.amazonaws.com/dev/blog-generation"

# aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
# aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")

#intialize the s3 client
s3_client = boto3.client(
    "s3",
    region_name="us-east-1",
    aws_access_key_id=aws_access_key,
    aws_secret_access_key=aws_secret_key
)


# Sent post request to lambda function
# Function to send a request to AWS Lambda via API Gateway
def generate_blog(blog_topic):
    try:
        response = requests.post(API_GATEWAY_URL, json={"blog_topic": blog_topic})
        return response.status_code == 200
    except Exception as e:
        print(f"API Can't be reached:{e}")


# Now we pull data out of S3 bucket
# my AWS S3 bucket name
S3_BUCKET_NAME = "awsbedrockcourseak"

# func to get latest blog from S3
def get_latest_blog():
    response = s3_client.list_objects_v2(Bucket=S3_BUCKET_NAME, Prefix="blog-output/")

    if "Contents" in response and response["Contents"]:
        # find the latest file based on LastModified timestamp
        latest_file = max(response["Contents"], key=lambda x: x["LastModified"])
        latest_file_key = latest_file["Key"]  # This is the correct way to get the filename

        # download the latest file content
        file_obj = s3_client.get_object(Bucket=S3_BUCKET_NAME, Key=latest_file_key)
        blog_content = file_obj["Body"].read().decode("utf-8") #convert binary content to readable text

        return latest_file_key, blog_content
    return None, None

#-------------------# Streamlit UI #-------------------#

st.set_page_config("Bedrock GenBlog")

## Display the image and title
col1, col2 = st.columns([1, 6])
with col1:
    st.image("bedrock.jpg", width=100)  # Adjust the width as needed
with col2:
    st.title("MakeMyBlog with AWS Bedrock")
##-----------------------


# Blog Topic Input
blog_topic = st.text_input("Enter Blog Topic:")
st.session_state.blog_topic = blog_topic

if st.button("Generate Blog"):
    if blog_topic:
        with st.spinner("Sending Blog Generation Request to Bedrock... Please wait ⏳"):
            if generate_blog(blog_topic):
                st.success("✅ Blog generation request sent! Please wait a few moments.")
            else:
                st.error("❌ Failed to send request. Check API Gateway configuration.")
    else:
        st.warning("⚠️ Please enter a blog topic before submitting.")

# Fetch and Display Blog
#st.subheader("📄 Latest Generated Blog")

if st.button("Fetch My Blog"):
    with st.spinner("Fetching Blog from S3 ... ⏳"):
        file_name, blog_content = get_latest_blog()
    
    if blog_content:
        st.subheader(f"Your Blog on the topic : {st.session_state.blog_topic} is Ready")
        st.success(blog_content)
    else:
        st.warning("⚠️ No blog found in S3 yet. Try generating one first!")

