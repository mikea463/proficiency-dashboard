import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from roles_proficiency_data import df
from PIL import Image
import io
import base64
import re
import os

# Import AgGrid and related components
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode

# For email functionality
import sendgrid
from sendgrid.helpers.mail import Mail, Attachment, Content, Email, FileContent, FileName, FileType, Disposition

# Set page configuration
st.set_page_config(
    page_title="NeuZeit Interactive Team Readiness",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Display the NZ logo at the top of the app
st.image("NeuZeitLogoTB.png", width=300)
# Add the logo to the sidebar with a custom width
st.sidebar.image("NeuZeitLogoTB.png", width=150)

# Title and description
st.title("NeuZeit Interactive Team Readiness")
st.markdown("""
This app allows you to explore and model and gaps in your product or project team in 3 simple steps in order to address gaps before you execute and increase your probability of success. Ideal proficiency levels across roles and skills are modeled in the heatmap and editable in the table.

**1. Use the filters to the left to remove or add roles reflective of your team.**\n
**2. Remove any skill dimensions you do not want in your model (but we recommend keeping all of these skills).**\n
**3. Click and edit cell in the table to alter proficiency levels:** **L** → **M** → **H**.  Cells in the heatmap with a red border indicate a proficiency gap. (skill level should be addressed or augmented in order to maintain a high performing team).**\n
**Select the RADAR chart (below filters on the left) to see data represented in a RADAR format.**\n
""")

# Sidebar filters
st.sidebar.header("1. Select Team and Critical Dimensions")

# Select roles to display
roles = df['Role'].unique().tolist()
selected_roles = st.sidebar.multiselect("Select Roles", roles, default=roles)

# Select dimensions to display
dimensions = df.columns.tolist()[1:]  # Exclude the 'Role' column
selected_dimensions = st.sidebar.multiselect("Select Dimensions", dimensions, default=dimensions)

# Filter the DataFrame based on selections
filtered_df = df[df['Role'].isin(selected_roles)][['Role'] + selected_dimensions]

# Keep a copy of the initial proficiency levels
initial_df = filtered_df.copy()

# Map proficiency levels to numeric values for visualization
proficiency_map = {'L': 1, 'M': 2, 'H': 3}
inverse_proficiency_map = {1: 'L', 2: 'M', 3: 'H'}

# Convert initial proficiency levels to numeric values
initial_numeric_df = initial_df.copy()
for col in selected_dimensions:
    initial_numeric_df[col] = initial_numeric_df[col].map(proficiency_map)

# Function to cycle proficiency levels (Optional: You can keep this if needed)
# def cycle_proficiency(current_value):
#     if current_value == 'L':
#         return 'M'
#     elif current_value == 'M':
#         return 'H'
#     else:
#         return 'L'

st.subheader("Interactive Proficiency Levels Table")

# Configure AgGrid options
gb = GridOptionsBuilder.from_dataframe(filtered_df)
gb.configure_default_column(editable=True, resizable=True)

# Add cell renderer to handle click events
for col in selected_dimensions:
    gb.configure_column(
        col,
        cellRenderer="""
        function(params) {
            let eCell = document.createElement('span');
            eCell.innerHTML = params.value;
            eCell.style.cursor = 'pointer';
            eCell.addEventListener('click', function() {
                let currentValue = params.value.toUpperCase();  // Ensure currentValue is uppercase
                let nextValue = '';
                if (currentValue === 'L') {
                    nextValue = 'M';
                } else if (currentValue === 'M') {
                    nextValue = 'H';
                } else {
                    nextValue = 'L';
                }
                params.node.setDataValue(params.colDef.field, nextValue);
            });
            return eCell;
        }
        """
    )

grid_options = gb.build()

# Display the grid
grid_response = AgGrid(
    filtered_df,
    gridOptions=grid_options,
    data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
    update_mode=GridUpdateMode.MODEL_CHANGED,
    allow_unsafe_jscode=True,  # Set to True to allow custom JS functions
    fit_columns_on_grid_load=True,
    height=300,
    reload_data=False,
)

# Get the updated DataFrame after interaction
updated_df = grid_response['data']

# **NEW: Convert all proficiency entries to uppercase to ensure case-insensitivity**
for col in selected_dimensions:
    updated_df[col] = updated_df[col].astype(str).str.upper()  # Ensure conversion even if entries are not strings

# Map updated proficiency levels to numeric values
df_numeric_updated = updated_df.copy()
for col in selected_dimensions:
    df_numeric_updated[col] = updated_df[col].map(proficiency_map)

# Compare updated proficiency levels to initial proficiency levels
difference_df = df_numeric_updated.set_index('Role')[selected_dimensions] - initial_numeric_df.set_index('Role')[selected_dimensions]

# Create a mask where proficiency has decreased
decreased_mask = difference_df < 0

# Heatmap visualization
st.subheader("Heatmap of Proficiency Levels")

# Define a custom color palette for the heat map
custom_palette = sns.color_palette(["#e8e8e8", "#29b792", "#264a5e"])  # NZ Colors

fig, ax = plt.subplots(figsize=(10, len(selected_roles) * 0.5 + 1))
# Load our logo
logo = Image.open("NeuZeitLogoTB.png")
logo_resized = logo.resize((400, 100))  # Resize the logo as needed
fig.figimage(logo_resized, xo=50, yo=50, alpha=0.6, zorder=10)  # Adjust position and transparency

# Create a custom colormap
cmap = sns.color_palette(custom_palette, as_cmap=True)

# Plot the heatmap
sns.heatmap(
    df_numeric_updated.set_index('Role')[selected_dimensions],
    annot=updated_df.set_index('Role')[selected_dimensions],
    fmt='',
    cmap=cmap,
    cbar_kws={'label': 'Proficiency Level'},
    linewidths=0.5,
    linecolor='white',
    ax=ax
)

# Highlight cells where proficiency has decreased
for i in range(len(df_numeric_updated)):
    for j in range(len(selected_dimensions)):
        initial_value = initial_numeric_df.iloc[i][selected_dimensions[j]]
        updated_value = df_numeric_updated.iloc[i][selected_dimensions[j]]
        if updated_value < initial_value:
            # Get the patch corresponding to the cell
            ax.add_patch(plt.Rectangle((j, i), 1, 1, fill=False, edgecolor='red', lw=3))

# Adjust the plot
plt.xticks(rotation=45, ha='right')
plt.xlabel('Dimensions')
plt.ylabel('Roles')
plt.title('Proficiency Levels Heatmap')

# Display the plot
st.pyplot(fig)

# Save the heatmap to a BytesIO object
heatmap_buffer = io.BytesIO()
fig.savefig(heatmap_buffer, format='png')
heatmap_buffer.seek(0)

# Radar chart option
st.sidebar.subheader("Radar Chart Options")

if len(selected_roles) > 0 and len(selected_dimensions) > 2:
    show_radar = st.sidebar.checkbox("Show Radar Chart", value=False)
    if show_radar:
        # Function to plot radar chart for selected roles
        def plot_radar_chart(df, roles, dimensions):
            categories = dimensions
            N = len(categories)

            # Angle of each axis in the plot
            angles = [n / float(N) * 2 * np.pi for n in range(N)]
            angles += angles[:1]  # Complete the loop

            # Define figure size and DPI
            figsize = (6, 6)  # Width = 6 inches, Height = 6 inches

            fig_radar = plt.figure(figsize=figsize)
            ax = plt.subplot(111, polar=True)

            # Draw one axe per variable and add labels
            plt.xticks(angles[:-1], categories, color='grey', size=8)

            # Draw ylabels
            ax.set_rlabel_position(30)
            plt.yticks([1, 2, 3], ["Low", "Medium", "High"], color="grey", size=7)
            plt.ylim(0, 3)

            # Plot data for each role
            for index, row in df.iterrows():
                values = row[dimensions].tolist()
                values += values[:1]
                ax.plot(angles, values, linewidth=1, linestyle='solid', label=index)
                ax.fill(angles, values, alpha=0.1)

            # Load your company's logo
            logo = Image.open("NeuZeitLogoTB.png")
            logo_resized = logo.resize((200, 50))  # Resize the logo as needed

            fig_radar.figimage(logo_resized, xo=20, yo=20, alpha=0.6, zorder=10)  # Adjust position and transparency

            plt.title('Radar Chart of Proficiency Levels', size=14, y=1.1)
            plt.legend(loc='upper right', bbox_to_anchor=(1.7, 1.0))
            st.pyplot(fig_radar)

            # Save the radar chart to a BytesIO object
            radar_buffer = io.BytesIO()
            fig_radar.savefig(radar_buffer, format='png')
            radar_buffer.seek(0)

            return radar_buffer

        radar_buffer = plot_radar_chart(df_numeric_updated.set_index('Role'), selected_roles, selected_dimensions)
    else:
        st.info("Select 'Show Radar Chart' to display the radar chart. Note: At least 3 dimensions are required.")
else:
    st.info("Radar chart requires at least one role and more than two dimensions.")

# Email functionality
st.subheader("Send Your Edits via Email")

email = st.text_input("Enter your email address to receive your edits:")

# User acceptance message
st.markdown("""
By providing your email address and clicking the button below, you agree to receive your edited data and visualizations via email and receive a follow up email from NeuZeit. We will not share your email address with third parties.
""")

accept_terms = st.checkbox("I agree to the terms and conditions.")

def is_valid_email(email):
    regex = r'^\S+@\S+\.\S+$'
    return re.match(regex, email) is not None

if email and is_valid_email(email):
    if accept_terms:
        # **MODIFICATION 1: Disable the send email button by setting disabled=True**
        if st.button("Send My Edits via Email", disabled=True):
            st.warning("Email functionality is currently disabled.")
        st.info("The email feature has been temporarily disabled. Please try again later.")
        # Alternatively, you can provide a message without the button:
        # st.button("Send My Edits via Email", disabled=True)
    else:
        st.warning("Please accept the terms and conditions to proceed.")
else:
    if email:
        st.warning("Please enter a valid email address to receive your edits.")
    else:
        st.info("Enter your email address to receive your edits.")

# Footer
st.markdown("---")
st.markdown("Developed with ❤️ using Streamlit and AgGrid")