import boto3
import botocore.config
import json
from datetime import datetime

## To write the code I referred documentation below
# https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-meta.html

def blog_generate_using_bedrock(blogtopic:str)->str:
    """
    Generates a blog using Mistral 7B (v0:2) on Amazon Bedrock..
    """
    # Mistral 7B requires the `[INST] ... [/INST]` structure
    prompt_template = f"<s>[INST] Write a 200-word blog on the topic: {blogtopic} [/INST]"
    
    # Format the request payload for Mistral 7B
    body = {
        "prompt": prompt_template,
        "max_tokens": 200,  # Limits the blog length
        "temperature": 0.5,  # Controls randomness
        "top_p": 0.9,  # Nucleus sampling
        "top_k": 50  # Controls diversity
    }

    try:
        # Initialize a Bedrock Runtime client for invoking foundation models
        bedrock=boto3.client("bedrock-runtime",region_name="us-east-1",
                             config=botocore.config.Config(read_timeout=300,retries={'max_attempts':3}))
        
        # Calling the model for inference (making it generate a response)
        # Invoke Mistral 7B (v0:2) model
        response = bedrock.invoke_model(modelId="mistral.mistral-7b-instruct-v0:2",body=json.dumps(body))

        # Extract the actual response content from the model's output
        response_content=response.get('body').read()

        # Convert the AI model's response from JSON format into a Python dict
        response_data=json.loads(response_content)
        print(response_data)

        #pull the 'generation' key out which has our answer
        blog_details = response_data['outputs'][0]['text']
        return blog_details
    
    except Exception as e:
        #print the error occured
        print(f"Error generating the blog:{e}")
        #return blog empty str
        return ""
    
def save_blog_details_s3(s3_key,s3_bucket,generate_blog):

    """
    Saves the generated blog content to an Amazon S3 bucket.
    
    Parameters:
    - s3_key: The file name (or path) where the blog will be stored in S3.
    - s3_bucket: The name of the S3 bucket where the blog will be saved.
    - generate_blog: The actual blog content that needs to be stored.
    """

    # Create an S3 client to interact with Amazon S3
    s3=boto3.client('s3')

    try:
        # Upload the blog content to S3 with the specified file name and bucket
        s3.put_object(Bucket=s3_bucket,Key=s3_key,Body=generate_blog)
        print("Code saved to s3") # Confirmation message        
    except Exception as e:
        # Print an error message if something goes wrong
        print("Error when saving the code to s3")  
    

# this is from aws lamba function Code interface
def lambda_handler(event, context):

    """
    AWS Lambda function to generate a blog using Amazon Bedrock and save it to S3.
    
    Parameters:
    - event: The incoming request payload (contains blog topic).
    - context: AWS Lambda runtime context (not used in this function).
    
    Returns:
    - A response with HTTP status code 200 confirming the blog generation process.
    """


    # TODO implement

    # Extract the event body and convert it from JSON format into a Python dictionary
    event=json.loads(event['body'])
    # Retrieve the 'blog_topic' value from the event payload
    blogtopic=event['blog_topic']

     # Generate a blog using the Bedrock AI model (calls a separate function)
    generate_blog=blog_generate_using_bedrock(blogtopic=blogtopic)

    # If a blog was successfully generated, proceed to save it
    if generate_blog:
        # Get the current time (HHMMSS format) to create a unique file name
        current_time=datetime.now().strftime('%H%M%S')

        # Define the file path (S3 key) where the blog will be saved in S3
        s3_key=f"blog-output/{current_time}.txt"

        # Specify the name of the S3 bucket where the file will be stored
        s3_bucket='awsbedrockcourseak'

        # Save the generated blog content to the specified S3 bucket
        save_blog_details_s3(s3_key,s3_bucket,generate_blog)

    else:
        # If the blog generation fails, print a message 
        print("No Blog was generated")

     # Return a response confirming that the blog generation process is completed
    return{
        'statusCode':200,
        'body':json.dumps('Blog Generation is completed')
    }


        