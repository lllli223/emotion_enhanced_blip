
import json
import argparse
import logging
import os
from typing import Dict, List, Any

# --- Basic Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def add_titles(
    annotations_path: str,
    titles_path: str,
    mapping_path: str, # Assuming this file maps image_id to instance_id
    output_path: str
) -> None:
    """
    Adds titles from the titles file to the annotations file using a mapping file.

    Args:
        annotations_path: Path to the preprocessed annotations JSON file.
        titles_path: Path to the JSON file containing titles and image_ids.
        mapping_path: Path to the JSON file mapping image_id to instance_id.
        output_path: Path to save the updated annotations JSON file.
    """
    logger.info(f"Loading annotations from: {annotations_path}")
    try:
        with open(annotations_path, 'r', encoding='utf-8') as f:
            annotations_data: Dict[str, Dict[str, Any]] = json.load(f)
    except FileNotFoundError:
        logger.error(f"Annotations file not found: {annotations_path}")
        return
    except json.JSONDecodeError:
        logger.error(f"Error decoding JSON from annotations file: {annotations_path}")
        return

    logger.info(f"Loading titles from: {titles_path}")
    try:
        with open(titles_path, 'r', encoding='utf-8') as f:
            titles_data: List[Dict[str, Any]] = json.load(f)
    except FileNotFoundError:
        logger.error(f"Titles file not found: {titles_path}")
        return
    except json.JSONDecodeError:
        logger.error(f"Error decoding JSON from titles file: {titles_path}")
        return

    logger.info(f"Loading mapping data from: {mapping_path}")
    try:
        # *** Assumption: mapping_path JSON is a list of dicts like [{'image_id': 0, 'instance_id': 'hex_string'}, ...]***
        with open(mapping_path, 'r', encoding='utf-8') as f:
            mapping_data: List[Dict[str, Any]] = json.load(f)
    except FileNotFoundError:
        logger.error(f"Mapping file not found: {mapping_path}. Cannot map titles to annotations.")
        return
    except json.JSONDecodeError:
        logger.error(f"Error decoding JSON from mapping file: {mapping_path}")
        return
    except Exception as e:
        logger.error(f"Unexpected error loading mapping file {mapping_path}: {e}")
        return

    # --- Prepare Lookups ---
    try:
        # Create a lookup dictionary for titles: {image_id: title}
        image_id_to_title: Dict[int, str] = {
            item['image_id']: item['generated_title']
            for item in titles_data
            if 'image_id' in item and 'generated_title' in item
        }
        logger.info(f"Created title lookup with {len(image_id_to_title)} entries.")

        # Create a mapping from instance_id to image_id
        # *** Adjust this based on the actual structure of mapping_data if the assumption is wrong ***
        instance_id_to_image_id: Dict[str, int] = {
            item['instance_id']: item['image_id']
            for item in mapping_data
            if 'instance_id' in item and 'image_id' in item
        }
        logger.info(f"Created instance_id to image_id mapping with {len(instance_id_to_image_id)} entries.")

    except KeyError as e:
        logger.error(f"Missing expected key '{e}' in titles or mapping data. Please check file formats.")
        return
    except Exception as e:
        logger.error(f"Error creating lookups: {e}")
        return


    # --- Add Titles to Annotations ---
    updated_count = 0
    missing_mapping_count = 0
    missing_title_count = 0
    for instance_id, annotation in annotations_data.items():
        if instance_id in instance_id_to_image_id:
            image_id = instance_id_to_image_id[instance_id]
            if image_id in image_id_to_title:
                annotation['title'] = image_id_to_title[image_id]
                updated_count += 1
            else:
                logger.warning(f"No title found for image_id {image_id} (instance_id: {instance_id})")
                missing_title_count += 1
        else:
            logger.warning(f"No image_id mapping found for instance_id: {instance_id}")
            missing_mapping_count += 1

    logger.info(f"Added titles to {updated_count} annotations.")
    if missing_mapping_count > 0:
        logger.warning(f"Could not find mapping for {missing_mapping_count} instance_ids.")
    if missing_title_count > 0:
        logger.warning(f"Could not find titles for {missing_title_count} mapped image_ids.")

    # --- Save Updated Annotations ---
    logger.info(f"Saving updated annotations to: {output_path}")
    try:
        # Ensure the output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(annotations_data, f, indent=2, ensure_ascii=False)
        logger.info("Annotations successfully updated and saved.")
    except IOError as e:
        logger.error(f"Failed to write updated annotations to {output_path}: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred while saving the file: {e}")


def main():
    parser = argparse.ArgumentParser(description="Add titles to preprocessed annotations.")
    parser.add_argument(
        "--annotations_path",
        type=str,
        default="../annotations/preprocessed_annotations.json",
        help="Path to the input preprocessed annotations JSON file."
    )
    parser.add_argument(
        "--titles_path",
        type=str,
        default="../annotations/titles_0_to_2339_title.json",
        help="Path to the JSON file containing titles and image_ids."
    )
    parser.add_argument(
        "--mapping_path",
        type=str,
        default="../annotations/results_0_to_2339.json", # Assuming this file provides the mapping
        help="Path to the JSON file mapping image_id to instance_id."
    )
    parser.add_argument(
        "--output_path",
        type=str,
        default="../annotations/preprocessed_annotations_with_titles.json", # Default to a new file
        help="Path to save the updated annotations JSON file."
    )
    args = parser.parse_args()

    add_titles(args.annotations_path, args.titles_path, args.mapping_path, args.output_path)

if __name__ == "__main__":
    main()
