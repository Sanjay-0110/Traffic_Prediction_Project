import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
from tensorflow.keras.saving import load_model
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

# Load the trained LSTM model
model = load_model("C:/Projects/Personel_Project/Traffic_Congestion_Prediction/pythonProject/MyLSTM_1.keras")

# Set Streamlit page config
st.set_page_config(page_title="Model Accuracy & Findings", page_icon="📊", layout="wide")

st.sidebar.title("Navigation")
st.sidebar.page_link("webapp.py", label="🚗 Traffic Prediction")
st.sidebar.page_link("Pages/accurary.py", label="📊 Model Accuracy & Findings")
st.sidebar.page_link("Pages/Traffic_flow_dashboard.py", label="🔲 Dashboard Page")

# Title of the new page
st.title("📊 Model Accuracy & Findings")

# Placeholder Accuracy Graph (Replace with actual accuracy/loss data)
epochs = np.arange(1, 21)
train_loss = np.random.uniform(0.2, 0.6, size=20)  # Example training loss
val_loss = np.random.uniform(0.3, 0.7, size=20)  # Example validation loss

fig, ax = plt.subplots()
ax.plot(epochs, train_loss, label="Training Loss", marker="o", linestyle="--")
ax.plot(epochs, val_loss, label="Validation Loss", marker="s", linestyle="-")
ax.set_xlabel("Epochs")
ax.set_ylabel("Loss")
ax.set_title("Training & Validation Loss Over Epochs")
ax.legend()

st.pyplot(fig, use_container_width=True)

# Findings Section
st.header("🔍 Key Findings")
st.markdown("""
### Test Result and Analysis:
The Metro Interstate Traffic Volume Data Set is an hourly Interstate 94 Westbound traffic volume for MN DoT ATR station 301, roughly midway between Minneapolis and St Paul, MN. Our main aim was to build a multi-step RNN with LSTM model that predicts traffic volume 2 hours into the future using a 6-hour input window.

At the initial data processing stage, we found **7,629 duplicate hourly entries**, meaning traffic volume was repeated for the same hour. Initially, we treated it as an hour-per-record dataset, leading to modest validation results (**mid-300s MAE**). After properly preprocessing it as a time-series dataset indexed at **1-hour intervals**, validation results improved significantly (**low-200s MAE**).

### Data Preprocessing:
- **Missing Data:** A **10-month gap (2014-2015)** caused validation inconsistencies.
- **Outliers:** Adjusted temperature anomalies and extreme rain values.
- **Feature Engineering:**
  - One-hot encoding for `weather_main`.
  - `is_holiday` and `is_weekend` features created for better model performance.
  - `date_time` transformed using sine/cosine encoding to capture cyclical patterns.
  - Expanded features from **9 to 27**.
""")
col1, col2 = st.columns(2)

# Add images to each column
with col1:
    st.image("Output_images/img_1.png", caption="This gives the model access to the most important frequency features.  Note the obvious peaks at frequencies near 1/year and 1/day", use_container_width=True)

with col2:
    st.image("Output_images/img_2.png", caption="Time of day signal", use_container_width=True)
st.markdown("""
### Model Development:
We experimented with various **hyperparameters** to optimize performance:
- **LSTM units & layers:** A balance between complexity and overfitting.
- **Bi-Directional LSTM (Model 2):** Improved results compared to basic LSTM.
- **MyLSTM_1 & MyLSTM_2:** Custom models outperforming baseline TensorFlow models.

Our best-performing model:
- **Bidirectional LSTMs** with two custom forward and backward layers.
- **Two dense layers (512 units each) and a final dense output layer.**
- **Maintained low variance over more epochs.**
""")
st.image("C:/Projects/Personel_Project/Traffic_Congestion_Prediction/pythonProject/Output_images/img.png", caption="Model Performance and Predictions", use_container_width=False)
st.markdown("""
### Conclusion:
- **Bi-Directional LSTM performed best** with the least variance.
- **More LSTM units (not deeper layers) improved results.**
- **GRU and LSTM helped mitigate the vanishing gradient problem.**
- **Smaller LSTM models overfitted less and performed better on validation data.**

Future work can explore automated hyperparameter tuning and hybrid models incorporating CNNs for feature extraction.
""")


