import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from roles_proficiency_data import df
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
    page_title="Interactive Dashboard of Proficiency Levels",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Title and description
st.title("Interactive Dashboard of Proficiency Levels")
st.markdown("""
This dashboard allows you to explore and modify the proficiency levels required for various roles across key dimensions in a project team.

- **Click on a cell in the table to cycle through proficiency levels:** **L** → **M** → **H** → **L**.
- **Cells in the heatmap that have decreased in proficiency level compared to the initial dataset are highlighted in red.**
""")

# Sidebar filters
st.sidebar.header("Filters")

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

# Function to cycle proficiency levels
def cycle_proficiency(current_value):
    if current_value == 'L':
        return 'M'
    elif current_value == 'M':
        return 'H'
    else:
        return 'L'

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
                let currentValue = params.value;
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

# Map updated proficiency levels to numeric values
df_numeric_updated = updated_df.copy()
for col in selected_dimensions:
    df_numeric_updated[col] = df_numeric_updated[col].map(proficiency_map)

# Compare updated proficiency levels to initial proficiency levels
difference_df = df_numeric_updated.set_index('Role')[selected_dimensions] - initial_numeric_df.set_index('Role')[selected_dimensions]

# Create a mask where proficiency has decreased
decreased_mask = difference_df < 0

# Heatmap visualization
st.subheader("Heatmap of Proficiency Levels")

fig, ax = plt.subplots(figsize=(10, len(selected_roles) * 0.5 + 1))

# Create a custom colormap
cmap = sns.color_palette("YlGnBu", as_cmap=True)

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

            fig_radar = plt.figure(figsize=(6, 6))
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

            plt.title('Radar Chart of Proficiency Levels', size=14, y=1.1)
            plt.legend(loc='upper right', bbox_to_anchor=(1.3, 1.0))
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
By providing your email address and clicking the button below, you agree to receive your edited data and visualizations via email. We will not share your email address with third parties.
""")

accept_terms = st.checkbox("I agree to the terms and conditions.")

def is_valid_email(email):
    regex = r'^\S+@\S+\.\S+$'
    return re.match(regex, email) is not None

if email and is_valid_email(email):
    if accept_terms:
        if st.button("Send My Edits via Email"):
            # Send email with attachments
            # Replace with your actual API key or use environment variables
            SENDGRID_API_KEY = st.secrets["SENDGRID_API_KEY"]

            # Function to send email
            def send_email(to_email, subject, content, attachments=None):
                sg = sendgrid.SendGridAPIClient(api_key=SENDGRID_API_KEY)
                from_email = Email("no-reply@yourdomain.com")  # Use your verified sender email
                to_email = Email(to_email)
                mail = Mail(from_email, to_email, subject, Content("text/html", content))

                # Add attachments if any
                if attachments:
                    for attachment in attachments:
                        mail.add_attachment(attachment)

                response = sg.client.mail.send.post(request_body=mail.get())
                return response.status_code

            # Prepare attachments
            # Function to create attachment
            def create_attachment(file_bytes, file_name, mime_type):
                encoded_file = base64.b64encode(file_bytes).decode()
                attachment = Attachment()
                attachment.file_content = FileContent(encoded_file)
                attachment.file_type = FileType(mime_type)
                attachment.file_name = FileName(file_name)
                attachment.disposition = Disposition("attachment")
                return attachment

            attachments = []

            # CSV attachment
            csv_bytes = updated_df.to_csv(index=False).encode('utf-8')
            attachments.append(create_attachment(csv_bytes, 'updated_proficiency_levels.csv', 'text/csv'))

            # Heatmap attachment
            attachments.append(create_attachment(heatmap_buffer.getvalue(), 'heatmap.png', 'image/png'))

            # Radar chart attachment (if available)
            if show_radar and 'radar_buffer' in locals():
                attachments.append(create_attachment(radar_buffer.getvalue(), 'radar_chart.png', 'image/png'))

            subject = "Your Proficiency Levels Edits"
            content = """
            <p>Dear user,</p>
            <p>Please find attached your edited proficiency levels data and visualizations.</p>
            <p>Best regards,<br>Your Company</p>
            """

            try:
                status_code = send_email(email, subject, content, attachments)
                if status_code == 202:
                    st.success("Email sent successfully!")
                else:
                    st.error(f"Failed to send email. Status code: {status_code}")
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
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
