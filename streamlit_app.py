# Streamlit smoothie order form with Snowpark integration
# Co-authored with CoCo
# Import python packages
import requests 
import streamlit as st
from snowflake.snowpark.functions import col

#import os

# Write directly to the app
st.title(":cup_with_straw: Customize your Smoothie :cup_with_straw: ")
st.write(
  """Choose the fruits you want in your custom Smoothie!  """
)


name_on_order = st.text_input('Name on Smoothie: ')
st.write('The name on your smoothie will be: ', name_on_order)

cnx = st.connection("snowflake")
session = cnx.session()
my_dataframe = session.table("smoothies.public.fruit_options").select(col('FRUIT_NAME'),col('SEARCH_ON'))
#st.dataframe(data=my_dataframe, use_container_width=True)
#st.stop()
#fruit_list = my_dataframe.to_pandas()['FRUIT_NAME'].tolist()

#Convert the Snowpark Dataframe to a Pandas Dataframe so we can use the LOC function
pd_df=my_dataframe.to_pandas()
#st.dataframe(pd_df)
#st.stop()

# Extract fruit_list from pandas dataframe
fruit_list = pd_df['FRUIT_NAME'].tolist()

ingredients_list = st.multiselect(
'Choose up to 5 ingredients:',
 fruit_list,
max_selections=5
)

if ingredients_list:
    ingredients_string = ''

    for fruit_chosen in ingredients_list:
        ingredients_string += fruit_chosen + ' '

        search_on=pd_df.loc[pd_df['FRUIT_NAME'] == fruit_chosen, 'SEARCH_ON'].iloc[0]
        st.write('The search value for ', fruit_chosen,' is ', search_on, '.')

        st.subheader(fruit_chosen + ' Nutrition Information')
        smoothiefroot_response = requests.get(f"https://my.smoothiefroot.com/api/fruit/{SEARCH_ON}")
        
        if smoothiefroot_response.status_code == 200:
            st.dataframe(data=smoothiefroot_response.json(), use_container_width=True)
        else:
            st.error(f"Could not fetch nutrition info for {fruit_chosen}")
      
    #st.write(ingredients_string)

    # Use parameterized query to prevent SQL injection
    my_insert_stmt = "insert into smoothies.public.orders(ingredients, name_on_order) values (?, ?)"

    # st.write(my_insert_stmt)
    
    if name_on_order.strip():
        time_to_insert = st.button('Submit Order')

        if time_to_insert:
            session.sql(my_insert_stmt, [ingredients_string.strip(), name_on_order]).collect()
            
            st.success('Your Smoothie is ordered!', icon="✅")
    else:
        st.warning("Please enter a name for your smoothie before submitting")
