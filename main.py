import streamlit as st
from functions import ideator, create_produce_link_url
import json
import os
import sys
from datetime import datetime
from supabase import create_client, Client

#connect to supabase database
urL: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")

supabase: Client = create_client(urL, key)




def main():
    # Create a title for the chat interface
    st.title("Full Harvest Bot (named Harvey)")
    st.write("To test, first select some fields then click the button below.")
  

    name = st.text_input('Bot Name', value = 'Harvey')
    booking_link = st.text_input('Booking Link', value = 'fullharvestbookinglink.com')
    buyer_or_supplier = st.selectbox('Buyer or Supplier', ['Buyer', 'Supplier'], index = 0)
    lead_first_name = st.text_input('Lead First Name', value = 'John')
    buyer_company_name = st.text_input('Company Name', value = 'Appleseed Co')

    options = ['Tomatoes', 'Blueberries', 'Garlic', 'Bananas', 'Onions']
    selection = st.multiselect("Choose your options", options)

    if len(selection) == 0:
        selected_commodities = ''
    elif len(selection) == 1:
        selected_commodities = selection[0]
    elif len(selection) == 2:
        selected_commodities = f"{selection[0]} and {selection[1]}"
    else:
        selected_commodities = ', '.join(selection[:-1]) + f", and {selection[-1]}"


    need_availability = st.selectbox('Need or Availability', ['weekly','monthly', 'quarterly', 'yearly'], index = 1)
    growing_method = st.selectbox('Growing Method', ['Organic', 'Conventional', 'Does not matter'], index = 1)
    search_produce_link = "https://app.fullharvest.com/listings/?anonymous=true"
    bid_request_link = 'https://app.fullharvest.com/bid_requests/new/specs'

    lead_dict_info = {
        'name': name,
        'booking_link': booking_link,
        'buyer_or_supplier':  buyer_or_supplier,
        'lead_first_name': lead_first_name,
        'buyer_company_name': buyer_company_name,
        'selected_commodities': selected_commodities,
        'need_availability': need_availability,
        'growing_method': growing_method

    }

    
    if st.button('Click to Start or Restart'):
        if buyer_or_supplier == "Buyer":
            bot = 'harvey_buyer'
        if buyer_or_supplier == "Supplier":
            bot = 'harvey_supplier'
            
        print(bot)
        data, count = supabase.table("bots_dev").select("*").eq("id", bot).execute()   
        bot_info = data[1][0]
        
        system_prompt = bot_info['system_prompt']
        if len(selection) > 0:
            initial_text = bot_info['initial_text']
        else:
            initial_text = "Hey, this is {name} from Full Harvest. Just saw you signed up on our platform. Am I speaking with {lead_first_name}?"

        system_prompt = system_prompt.format(bid_request_link = bid_request_link, search_produce_link = search_produce_link, need_availability = need_availability, growing_method = growing_method, buyer_or_supplier = buyer_or_supplier, selected_commodities = selected_commodities, lead_first_name=lead_first_name, booking_link = booking_link, name=name, buyer_company_name = buyer_company_name)

        initial_text = initial_text.format(lead_first_name = lead_first_name, name=name, selected_commodities = selected_commodities, need_availability = need_availability)

        st.write(initial_text)


        #clear database to only first two lines
        with open('database.jsonl', 'w') as f:
        # Override database with initial json files
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "assistant", "content": initial_text}            
            ]
            f.write(json.dumps(messages[0])+'\n')
            f.write(json.dumps(messages[1])+'\n')


    # Create a text input for the user to enter their message and append it to messages
    userresponse = st.text_input("Enter your message")
    

    # Create a button to submit the user's message
    if st.button("Send"):
        #prep the json
        newline = {"role": "user", "content": userresponse}

        #append to database
        with open('database.jsonl', 'a') as f:
        # Write the new JSON object to the file
            f.write(json.dumps(newline) + '\n')

        #extract messages out to list
        messages = []

        with open('database.jsonl', 'r') as f:
            for line in f:
                json_obj = json.loads(line)
                messages.append(json_obj)

        #generate OpenAI response
        messages, count = ideator(messages, lead_dict_info)

        #append to database
        with open('database.jsonl', 'a') as f:
                for i in range(count):
                    f.write(json.dumps(messages[-count + i]) + '\n')



        # Display the response in the chat interface
        string = ""

        for message in messages[1:]:
            if 'This is a secret internal thought' not in str(message):
                string = string + message["role"] + ": " + message["content"] + "\n\n"
        st.write(string)
        

if __name__ == '__main__':
    main()
