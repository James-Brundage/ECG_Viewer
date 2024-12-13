import matplotlib
matplotlib.use('Agg')  # Use a non-interactive backend

from flask import Flask, render_template, request, jsonify, send_file
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
import os
import numpy as np

app = Flask(__name__, static_folder='static')
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Route for the homepage
@app.route('/')
def index():
    return render_template('index.html')

# Route to handle file upload
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(filepath)

    df = pd.read_csv(filepath)

    df['Quality_Score']= 'No Quality'
    df['Note'] = 'No Note'
    df['original_index'] = df.index

    df.to_csv(filepath, index=False)
    return jsonify({'columns': list(df.columns)})

# Route to generate scatterplot
@app.route('/scatterplot', methods=['POST'])
def scatterplot():
    data = request.get_json()
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], data['filename'])
    df = pd.read_csv(filepath)

    x_col = data['x_col']
    y_col = data['y_col']
    color_col = data['color_col']

    # Map unique categories to discrete colors
    
    custom_colors = {
        'No Quality': 'black',
        'Good': 'green',
        'Bad': 'red',
    }
    
    # Assign colors based on the custom color map
    df['color'] = df[color_col].map(custom_colors)


    scatter_data = {
    "x": df[x_col].tolist(),
    "y": df[y_col].tolist(),
    "customdata": df['original_index'].tolist(),  # Pass the original indices
    "mode": "markers",
    "type": "scatter",
    "marker": {"color": df['color'].tolist(),
                "size":10},
    'text': df['Sex'].tolist(),  # Custom column for hover text
    'hoverinfo': 'x+y+text+customdata'  # Display x, y, and the custom text
    }

    scatter_layout = {
        "title": "Scatterplot",
        "xaxis": {"title": x_col},
        "yaxis": {"title": y_col}
    }

    figure = {"data": [scatter_data], "layout": scatter_layout}

    return figure

# Route to fetch ECG data
@app.route('/ecg', methods=['POST'])
def ecg():
    data = request.get_json()
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], data['filename'])
    
    print(data)
    # df is the uploaded file
    df = pd.read_csv(filepath)
    
    index = int(data['index'])
    print(index)
    
    ecg_abs_path = df.iloc[index]['ECG_Path']
    
    ecg_data=np.load(ecg_abs_path)

    n_leads, n_points = ecg_data.shape
    fig, axs = plt.subplots(n_leads, sharex=True)
    fig.set_figheight(15)
    fig.set_figwidth(10)
    for i in range(n_leads):
        axs[i].plot(ecg_data[i,:])

    fig.suptitle(f"ECG Data at Index {index}")
    
    plot_path = f"static/ecg_{index}.png"
    plt.savefig(plot_path)
    plt.close()

    if pd.isna(df.iloc[index]['Quality_Score']):
        quality_score = ''
    else:
        quality_score = df.iloc[index]['Quality_Score']

    if pd.isna(df.iloc[index]['Note']):
        note = ''
    else:
        note = df.iloc[index]['Note']

    return jsonify({
        'ecg_plot': plot_path,
        'quality_score': quality_score,
        'note': note,
        'original_index':index
    })

# Route to update quality score and notes
@app.route('/update_ecg', methods=['POST'])
def update_ecg():
    data = request.get_json()

    # Get the index, quality score, and note from the request
    index = int(data['index'])
    quality_score = data['quality_score']
    note = data['note']

    filepath = os.path.join(app.config['UPLOAD_FOLDER'], data['filename'])

    df=pd.read_csv(filepath)

    # Update the DataFrame with the new quality score and note
    df.loc[index, 'Quality_Score'] = quality_score
    df.loc[index, 'Note'] = note

    # print(index)
    # print(df.iloc[index])
    # print(df)
    # save_path = os.path.join(app.config['UPLOAD_FOLDER'],filepath)

    # Save the updated DataFrame back to the CSV
    df.to_csv(filepath, index=False)

    return jsonify({'message': 'ECG updated successfully'})

@app.route('/export', methods=['POST'])
def export_csv():
    # Get the filename from the request (you can also keep track of the uploaded filename in a session or global variable)
    data = request.get_json()
    filename = data.get('filename')
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    print(filepath)
    # Load the updated DataFrame
    df = pd.read_csv(filepath)
    print(df.head())
    # Save the DataFrame back to the CSV
    df.to_csv(filepath, index=False)

    # Send the updated CSV file back as a downloadable file
    return send_file(filepath, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
