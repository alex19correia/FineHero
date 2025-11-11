import argparse
import os
import json
from datetime import datetime
import sys
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from backend.services.pdf_processor import PDFProcessor
from backend.services.defense_generator import DefenseGenerator
from backend.app.schemas import Fine # Assuming Fine schema is still relevant for PDF processing
from backend.services.web_scraper import WebScraper
from rag.ingest import ingest_document_with_metadata, ingest_documents_from_directory, KNOWLEDGE_BASE_DIR

def main():
    """
    Main function for the FineHero CLI.
    """
    parser = argparse.ArgumentParser(description="FineHero AI CLI - Automate your traffic fine defenses and manage knowledge base.")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # --- Subparser for PDF Processing ---
    process_pdf_parser = subparsers.add_parser("process-pdf", help="Process a PDF traffic fine.")
    process_pdf_parser.add_argument("pdf_path", type=str, help="The full path to the PDF file of the traffic fine.")

    # --- Subparser for Web Scraping ---
    scrape_parser = subparsers.add_parser("scrape", help="Scrape legal documents from specified web sources.")
    scrape_subparsers = scrape_parser.add_subparsers(dest="scrape_source", help="Web scraping sources")

    # ANSR Scraper
    ansr_parser = scrape_subparsers.add_parser("ansr", help="Scrape documents from ANSR website.")
    ansr_parser.add_argument("--start-url", type=str, default="https://www.ansr.pt/documentos",
                             help="Starting URL for ANSR scraping.")
    ansr_parser.add_argument("--max-pages", type=int, default=2,
                             help="Maximum number of pages to scrape from ANSR.")
    ansr_parser.add_argument("--base-url", type=str, default="https://www.ansr.pt/",
                             help="Base URL for ANSR website.")

    # Diario da Republica Scraper
    diario_da_republica_parser = scrape_subparsers.add_parser("diario-da-republica", help="Scrape documents from Diário da República website.")
    diario_da_republica_parser.add_argument("--start-url", type=str, default="https://dre.pt/web/guest/home/-/dre/search",
                                            help="Starting URL for Diário da República scraping.")
    diario_da_republica_parser.add_argument("--max-pages", type=int, default=1,
                                            help="Maximum number of pages to scrape from Diário da República.")
    diario_da_republica_parser.add_argument("--base-url", type=str, default="https://dre.pt/",
                                            help="Base URL for Diário da República website.")

    # DGSI Scraper
    dgsi_parser = scrape_subparsers.add_parser("dgsi", help="Scrape documents from DGSI.pt website.")
    dgsi_parser.add_argument("--start-url", type=str, default="http://www.dgsi.pt/jstj.nsf/DecisoesSumario?OpenAgent&top=1000",
                             help="Starting URL for DGSI.pt scraping.")
    dgsi_parser.add_argument("--max-pages", type=int, default=1,
                             help="Maximum number of pages to scrape from DGSI.pt.")
    dgsi_parser.add_argument("--base-url", type=str, default="http://www.dgsi.pt/",
                             help="Base URL for DGSI.pt website.")

    # --- Subparser for Knowledge Base Ingestion ---
    ingest_parser = subparsers.add_parser("ingest", help="Ingest documents into the knowledge base.")
    ingest_subparsers = ingest_parser.add_subparsers(dest="ingest_type", help="Ingestion types")

    # Ingest from directory
    ingest_dir_parser = ingest_subparsers.add_parser("dir", help="Ingest all documents from the knowledge_base directory.")
    ingest_dir_parser.add_argument("--path", type=str, default=KNOWLEDGE_BASE_DIR,
                                   help="Path to the directory containing documents to ingest.")

    # Ingest single document with metadata
    ingest_single_parser = ingest_subparsers.add_parser("single", help="Ingest a single document with rich metadata.")
    ingest_single_parser.add_argument("--document-json", type=str, required=True,
                                      help="JSON string containing document content and metadata. "
                                           "Example: '{\"content\": \"...\", \"title\": \"...\", \"document_type\": \"law\", \"jurisdiction\": \"Portugal\", \"publication_date\": \"YYYY-MM-DD\", \"source_url\": \"http://example.com\"}'")

    args = parser.parse_args()

    if args.command == "process-pdf":
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
        # fine_data = Fine(**extracted_data, id=1) # Using a dummy ID, adjust as needed

        # 3. AI Defense Generation
        print("\n--- Generating AI Defense ---")
        try:
            # Assuming DefenseGenerator can take extracted_data directly or needs a Fine object
            # For now, creating a dummy Fine object. This part needs proper integration with DB.
            dummy_fine = Fine(
                id=1, # This ID should come from a database insertion
                date=datetime.now().date(), # Placeholder
                location=extracted_data.get("location", "Unknown"),
                infractor="Unknown",
                fine_amount=float(extracted_data.get("amount", 0.0)),
                infraction_code=extracted_data.get("infraction", "Unknown"),
                pdf_reference=os.path.basename(args.pdf_path)
            )
            generator = DefenseGenerator(dummy_fine)
            defense_text = generator.generate()
        except Exception as e:
            print(f"An error occurred during defense generation: {e}")
            return

        # 4. Output the final defense
        defense_filename = f"defense_{os.path.basename(args.pdf_path).replace('.pdf', '.txt')}"
        with open(defense_filename, "w", encoding="utf-8") as f:
            f.write(defense_text)
        
        print(f"\n✅ Success! Your generated defense has been saved to: {defense_filename}")

    elif args.command == "scrape":
        scraper = WebScraper(base_url=args.base_url) # Initialize scraper once
        
        if args.scrape_source == "ansr":
            print(f"Starting ANSR scraping from {args.start_url} (max pages: {args.max_pages})...")
            ansr_documents = scraper.scrape_ansr_documents(args.start_url, args.max_pages)
            source_name = "ANSR"
        elif args.scrape_source == "diario-da-republica":
            print(f"Starting Diário da República scraping from {args.start_url} (max pages: {args.max_pages})...")
            scraper.base_url = args.base_url # Update base_url for specific scraper
            ansr_documents = scraper.scrape_diario_da_republica_documents(args.start_url, args.max_pages)
            source_name = "Diario da Republica"
        elif args.scrape_source == "dgsi":
            print(f"Starting DGSI.pt scraping from {args.start_url} (max pages: {args.max_pages})...")
            scraper.base_url = args.base_url # Update base_url for specific scraper
            ansr_documents = scraper.scrape_dgsi_documents(args.start_url, args.max_pages)
            source_name = "DGSI.pt"
        else:
            print("Please specify a scraping source (e.g., 'ansr', 'diario-da-republica', 'dgsi').")
            return

        if ansr_documents:
            print(f"\n--- Found {len(ansr_documents)} {source_name} Documents. Ingesting... ---")
            download_dir = os.path.join(KNOWLEDGE_BASE_DIR, f"{source_name.lower().replace('.', '_').replace(' ', '_')}_downloads")
            os.makedirs(download_dir, exist_ok=True)

            for doc in ansr_documents:
                # For now, only ingest PDFs as text after downloading
                if doc['url'].endswith('.pdf'):
                    file_name = os.path.basename(urlparse(doc['url']).path)
                    save_path = os.path.join(download_dir, file_name)
                    if scraper.download_pdf(doc['url'], save_path):
                        # Placeholder for PDF text extraction before ingestion
                        # For now, we'll just use a dummy content
                        print(f"PDF downloaded to {save_path}. Placeholder for text extraction and ingestion.")
                        
                        # Dummy content for ingestion
                        dummy_content = f"Content of PDF from {doc['url']}"
                        
                        doc_data = {
                            "content": dummy_content,
                            "title": doc['title'],
                            "document_type": doc.get("document_type", "unknown"),
                            "jurisdiction": doc.get("jurisdiction", "Portugal"),
                            "publication_date": datetime.now().date(), # Needs actual extraction
                            "source_url": doc['url'],
                            "file_path": save_path,
                            "case_outcome": doc.get("case_outcome"),
                            "legal_arguments": doc.get("legal_arguments")
                        }
                        try:
                            ingest_document_with_metadata(doc_data)
                        except Exception as e:
                            print(f"Error ingesting document {doc['title']}: {e}")
                    else:
                        print(f"Skipping ingestion for {doc['title']} due to download failure.")
                else:
                    print(f"Skipping non-PDF document: {doc['title']} at {doc['url']}")
        else:
            print(f"No {source_name} documents found to ingest.")

    elif args.command == "ingest":
        if args.ingest_type == "dir":
            print(f"Ingesting documents from directory: {args.path}")
            ingest_documents_from_directory(args.path)
        elif args.ingest_type == "single":
            print("Ingesting single document...")
            try:
                doc_data = json.loads(args.document_json)
                # Convert publication_date string to date object if present
                if 'publication_date' in doc_data and isinstance(doc_data['publication_date'], str):
                    doc_data['publication_date'] = datetime.strptime(doc_data['publication_date'], '%Y-%m-%d').date()
                ingest_document_with_metadata(doc_data)
            except json.JSONDecodeError:
                print("Error: --document-json argument must be a valid JSON string.")
            except KeyError as e:
                print(f"Error: Missing key in document data: {e}")
            except Exception as e:
                print(f"An unexpected error occurred during single document ingestion: {e}")
        else:
            print("Please specify an ingestion type (e.g., 'dir' or 'single').")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
