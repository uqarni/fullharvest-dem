import openai
import os
import re
import random
from datetime import datetime, timedelta
import random
import time

#examples puller
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.document_loaders import TextLoader
from langchain.text_splitter import CharacterTextSplitter

def find_txt_examples(query, k=8):
    loader = TextLoader("sops.txt")
    documents = loader.load()
    text_splitter = CharacterTextSplitter(chunk_size=500, chunk_overlap=100)
    docs = text_splitter.split_documents(documents)
    
    embeddings = OpenAIEmbeddings()

    db = FAISS.from_documents(docs, embeddings)
    docs = db.similarity_search(query, k=k)

    examples = ""
    i = 1
    for doc in docs:
       examples += f'\n\nSNIPPET {i}' + doc.page_content
       i+=1
    return examples


#generate openai response; returns messages with openai response
def ideator(messages, lead_dict_info):
    print('message length: ' + str(len(messages)))
    prompt = messages[0]['content']
    messages = messages[1:]
    new_message = messages[-1]['content']

    #perform similarity search
    examples = find_txt_examples(new_message, k=5)
    examples = examples.format(**lead_dict_info)
    prompt = prompt + examples
    print('inbound message: ' + str(messages[-1]))
    print('prompt' + prompt)
    print('\n\n')
    prompt = {'role': 'system', 'content': prompt}
    messages.insert(0,prompt)
    
    print('total messages:\n',messages)
    for i in range(5):
      try:
        key = os.environ.get("OPENAI_API_KEY")
        openai.api_key = key
    
        result = openai.ChatCompletion.create(
          model="gpt-4",
          messages= messages,
          max_tokens = 500,
          temperature = 0
        )
        response = result["choices"][0]["message"]["content"]
        print('response:')
        print(response)
        print('\n\n')
        break
      except Exception as e: 
        error_message = f"Attempt {i + 1} failed: {e}"
        print(error_message)
        if i < 4:  # we don't want to wait after the last try
          time.sleep(5)  # wait for 5 seconds before the next attempt
  
    def split_sms(message):
        import re
  
        # Use regular expressions to split the string at ., !, or ? followed by a space or newline
        sentences = re.split('(?<=[.!?]) (?=\\S)|(?<=[.!?])\n', message.strip())
        # Strip leading and trailing whitespace from each sentence
        sentences = [sentence.strip() for sentence in sentences if sentence.strip()]
  
        # Compute the cumulative length of all sentences
        cum_length = [0]
        for sentence in sentences:
            cum_length.append(cum_length[-1] + len(sentence))
      
            total_length = cum_length[-1]
  
        # Find the splitting point
        split_point = next(i for i, cum_len in enumerate(cum_length) if cum_len >= total_length / 2)
  
        # Split the sentences into two parts at the splitting point
        part1 = sentences[:split_point]
        part2 = sentences[split_point:]
  
        # Join the sentences in each part back into strings and exclude any part that is empty
        strings = []
        if part1:
            strings.append(" ".join(part1))
        if part2:
            strings.append(" ".join(part2))
      
        return strings

    split_response = split_sms(response)
    count = len(split_response)
    for section in split_response:
        section = {
           "role": "assistant", 
           "content": section
           }
        messages.append(section)
    
    return messages, count
  


