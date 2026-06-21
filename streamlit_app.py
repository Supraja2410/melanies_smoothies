# Streamlit smoothie order form with Snowpark integration
# Co-authored with CoCo
# Import python packages
import requests
import streamlit as st
from snowflake.snowpark.functions import col
from urllib.parse import quote_plus

# Write directly to the app
st.title(":cup_with_straw: Customize your Smoothie :cup_with_straw: ")
st.write(
    """Choose the fruits you want in your custom Smoothie!  """
)

name_on_order = st.text_input('Name on Smoothie: ')
st.write('The name on your smoothie will be: ', name_on_order)

# Get a Snowflake connection/session
cnx = st.connection("snowflake")
session = cnx.session()

# Read fruit options from Snowpark (limit to avoid huge pandas conversions)
snow_df = session.table("smoothies.public.fruit_options").select(col('FRUIT_NAME'), col('SEARCH_ON')).limit(2000)

# Convert to pandas safely (with a guard to avoid extremely large conversions)
pd_df = snow_df.to_pandas()
if pd_df.shape[0] == 0:
    st.warning("No fruit options available.")
else:
    if pd_df.shape[0] > 1000:
        st.warning("Too many fruit options; using the first 1000 only.")
        pd_df = pd_df.head(1000)

# Extract fruit_list from pandas dataframe
fruit_list = pd_df['FRUIT_NAME'].tolist()

ingredients_list = st.multiselect(
    'Choose up to 5 ingredients:',
    fruit_list,
    max_selections=5
)

if ingredients_list:
    # Use comma-separated ingredients text
    ingredients_string = ', '.join(ingredients_list)

    for fruit_chosen in ingredients_list:
        # Safely get the SEARCH_ON value from the dataframe
        match = pd_df.loc[pd_df['FRUIT_NAME'] == fruit_chosen, 'SEARCH_ON']
        if match.empty:
            st.error(f"No search key available for {fruit_chosen}; skipping.")
            continue
        search_on = match.iloc[0]

        # Do NOT display raw search keys or other potentially sensitive DB values.
        st.write(f"{fruit_chosen} — fetching nutrition information...")

        # URL-encode the search value before calling external service to avoid injection/redirect issues
        encoded = quote_plus(str(search_on))

        # Request external API with timeout and error handling
        try:
            resp = requests.get(f"https://my.smoothiefroot.com/api/fruit/{encoded}", timeout=5)
        except requests.RequestException as e:
            st.error(f"Network error while fetching nutrition for {fruit_chosen}: {e}")
            continue

        if resp.status_code == 200:
            # Parse JSON safely
            try:
                json_data = resp.json()
            except ValueError:
                st.error(f"Invalid JSON received for {fruit_chosen}")
                continue

            # Only display moderate-sized payloads
            if isinstance(json_data, dict) and len(str(json_data)) < 10000:
                st.subheader(f"{fruit_chosen} Nutrition Information")
                st.dataframe(data=json_data, use_container_width=True)
            else:
                st.write(f"Nutrition data for {fruit_chosen} received (not displayed due to size).")
        else:
            st.error(f"Could not fetch nutrition info for {fruit_chosen} (status {resp.status_code})")

    # Use parameterized query to prevent SQL injection
    my_insert_stmt = "insert into smoothies.public.orders(ingredients, name_on_order) values (?, ?)"

    if name_on_order.strip():
        time_to_insert = st.button('Submit Order')

        if time_to_insert:
            # Execute parameterized insert safely
            session.sql(my_insert_stmt, [ingredients_string.strip(), name_on_order]).collect()
            st.success('Your Smoothie is ordered!', icon="✅")
    else:
        st.warning("Please enter a name for your smoothie before submitting")
