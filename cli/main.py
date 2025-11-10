import argparse
import os
from backend.services.pdf_processor import PDFProcessor
from backend.services.defense_generator import DefenseGenerator
from backend.app.schemas import Fine

def main():
    """
    Main function for the FineHero CLI.
    """
    parser = argparse.ArgumentParser(description="FineHero AI CLI - Automate your traffic fine defenses.")
    parser.add_argument("pdf_path", type=str, help="The full path to the PDF file of the traffic fine.")
    
    args = parser.parse_args()

    if not os.path.exists(args.pdf_path):
        print(f"Error: The file '{args.pdf_path}' does not exist.")
        return

    print(f"Processing fine from: {args.pdf_path}")

    # 1. PDF Ingestion and Data Extraction
    try:
        with open(args.pdf_path, "rb") as f:
            processor = PDFProcessor(f)
            extracted_data = processor.process()
            print("\n--- Extracted Information ---")
            print(extracted_data)
    except Exception as e:
        print(f"An error occurred during PDF processing: {e}")
        return

    # 2. Prepare data for AI Defense Generation
    # (Here we would also save the extracted data to the database)
    fine_data = Fine(**extracted_data, id=1) # Using a dummy ID

    # 3. AI Defense Generation
    print("\n--- Generating AI Defense ---")
    try:
        generator = DefenseGenerator(fine_data)
        defense_text = generator.generate()
    except Exception as e:
        print(f"An error occurred during defense generation: {e}")
        return

    # 4. Output the final defense
    defense_filename = f"defense_{os.path.basename(args.pdf_path).replace('.pdf', '.txt')}"
    with open(defense_filename, "w", encoding="utf-8") as f:
        f.write(defense_text)
    
    print(f"\n✅ Success! Your generated defense has been saved to: {defense_filename}")


if __name__ == "__main__":
    main()
