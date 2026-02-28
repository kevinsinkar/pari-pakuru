import os
from PyPDF2 import PdfReader, PdfWriter

def split_pdf(input_pdf, output_dir):
    # Create the output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    # Create a reader object
    reader = PdfReader(input_pdf)
    # Get the base filename without extension
    base_fname = os.path.splitext(os.path.basename(input_pdf))[0]

    # Iterate through each page
    for page_num in range(len(reader.pages)):
        writer = PdfWriter()
        writer.add_page(reader.pages[page_num])

        # Save each page individually in the output directory
        output_filename = os.path.join(output_dir, f'{base_fname}_page_{page_num + 1}.pdf')
        with open(output_filename, 'wb') as out:
            writer.write(out)
        print(f'Created: {output_filename}')

# Run the function with correct paths
input_file = 'Blue Book - Pari Pakuru.pdf'
output_directory = 'Blue Book - Pari Pakuru - split'

if __name__ == "__main__":
    split_pdf(input_file, output_directory)
