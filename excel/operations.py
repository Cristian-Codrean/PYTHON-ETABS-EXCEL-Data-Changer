import os
import xlwings as xw
import sqlite3
from datetime import datetime


def copy_excel_file(source_excel_path, destination_excel_path):
    """Creează o copie a unui fișier Excel folosind xlwings."""
    app = None
    source_wb = None

    try:
        print(f"-- Sursa: {source_excel_path}")
        print(f"-- Destinație: {destination_excel_path}")

        # Verifică dacă fișierul sursă există
        if not os.path.exists(source_excel_path):
            print(f"⮽⮽ Fișierul sursă nu există: {source_excel_path}")
            return False

        # Verifică dacă folderul destinație există
        destination_dir = os.path.dirname(destination_excel_path)
        if not os.path.exists(destination_dir):
            print(f"⮽⮽ Folderul destinație nu există: {destination_dir}")
            return False

        # Verifică dacă fișierul destinație există deja
        if os.path.exists(destination_excel_path):
            print(f"--  Fișierul destinație există deja, se suprascrie")
            os.remove(destination_excel_path)

        # Deschide aplicația Excel în background
        app = xw.App(visible=False)

        # Dezactivează alerts pentru a evita dialog boxes
        app.display_alerts = False

        print(f"-- Deschidere workbook-ul sursă")
        # Deschide workbook-ul sursă
        source_wb = app.books.open(source_excel_path)

        print(f"-- Salvare ca fișier nou")
        # Salvează ca fișier nou la locația specificată
        source_wb.save(destination_excel_path)

        print(f"-- Închidere workbook-ul")
        # Închide workbook-ul
        source_wb.close()

        # Verifică dacă copia a fost creată
        if os.path.exists(destination_excel_path):
            file_size = os.path.getsize(destination_excel_path)
            print(f"✓✓ Fișier Excel copiat cu succes: {destination_excel_path}")
            print(f"-- Dimensiune fișier: {file_size} bytes")
            return True
        else:
            print(f"⮽⮽ Eroare - fișierul destinație nu a fost creat")
            return False

    except Exception as e:
        print(f"⮽⮽ Eroare la copierea fișierului Excel cu xlwings: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # Clean up
        if source_wb is not None:
            try:
                source_wb.close()
            except:
                pass
        if app is not None:
            try:
                app.quit()
            except:
                pass


def frame_group(db_path="frames.db"):
    """
    Extracts and groups beam data from temporary database file.
    """
    try:
        if not os.path.exists(db_path):
            print(f"⮽⮽ Database file not found: {db_path}")
            return None

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Get all frames from database with UPDATED columns (using SelectedStory)
        cursor.execute("""
            SELECT id, UniqueName, Label, GroupID, OrderID, Scenario,
                   Rezistente, DCL, DCM, DCH, Secundare, DirX, DirY,
                   CombUpper, CombLower, SelectedStory
            FROM Frames 
            ORDER BY Scenario, GroupID, OrderID
        """)

        beams = cursor.fetchall()
        conn.close()

        print(f"-- Found {len(beams)} beams in database")

        # Group beams by scenario and group
        grouped_beams = {
            "groups": [],
            "total_beams": len(beams),
            "timestamp": datetime.now().isoformat()
        }

        # Group beams properly
        groups_dict = {}
        for beam in beams:
            scenario = beam[5]  # Scenario column (index 5)
            group_id = beam[3]  # GroupID column (index 3)

            key = f"{scenario}_{group_id}"
            if key not in groups_dict:
                groups_dict[key] = {
                    "group_id": group_id,
                    "scenario": scenario,
                    "beams": [],
                    "settings": {
                        "rezistente": beam[6],  # Rezistente
                        "dcl": beam[7],  # DCL
                        "dcm": beam[8],  # DCM
                        "dch": beam[9],  # DCH
                        "secundare": beam[10],  # Secundare
                        "dir_x": beam[11],  # DirX
                        "dir_y": beam[12],  # DirY
                        "comb_upper": beam[13],  # CombUpper
                        "comb_lower": beam[14],  # CombLower
                        "etaj": beam[15]  # SelectedStory (folosit ca "etaj" pentru compatibilitate)
                    }
                }

            beam_info = {
                "db_id": beam[0],
                "unique_name": beam[1],
                "label": beam[2],
                "selection_order": beam[4]  # OrderID (index 4)
            }
            groups_dict[key]["beams"].append(beam_info)

        # Convert to list
        for group_key, group_data in groups_dict.items():
            grouped_beams["groups"].append(group_data)

        print(f"-- Created {len(grouped_beams['groups'])} beam groups")
        return grouped_beams

    except Exception as e:
        print(f"⮽⮽ Error in frame_group function: {e}")
        import traceback
        traceback.print_exc()
        return None


def create_structured_excel_layout(excel_path, template_excel_path, db_path="frames.db"):
    """
    Creates structured Excel layout with beam data organized in rows and columns.
    """
    app = None
    wb = None
    template_wb = None

    try:
        print(f"-- Starting structured Excel layout creation for: {excel_path}")
        print(f"-- Using template: {template_excel_path}")

        # Get grouped beam data
        beam_groups = frame_group(db_path)
        if not beam_groups:
            print("⮽⮽ No beam data found for Excel creation")
            return False

        # Verify template exists
        if not os.path.exists(template_excel_path):
            print(f"⮽⮽ Template file not found: {template_excel_path}")
            return False

        # Ensure database has the new columns
        update_database_with_excel_positions(db_path)

        # Open Excel application
        app = xw.App(visible=False)
        app.display_alerts = False

        # Open the template workbook to read from
        template_wb = app.books.open(template_excel_path)
        print("-- Template workbook opened successfully")

        # Open the destination workbook to write to
        wb = app.books.open(excel_path)
        print("-- Destination workbook opened successfully")

        # Get all existing sheet names
        existing_sheets = [sheet.name for sheet in wb.sheets]
        print(f"-- Existing sheets: {existing_sheets}")

        # Process each combination and create/update sheets
        sheet_combinations = get_sheet_combinations(beam_groups)
        print(f"-- Found {len(sheet_combinations)} unique sheet combinations")

        # Track sheet names we've processed in THIS session to avoid duplicates
        processed_sheet_names = set()

        # Dictionary to collect all beam positions from all sheets
        all_beam_positions = {}

        for combo in sheet_combinations:
            sheet_name = combo["sheet_name"]

            if sheet_name in processed_sheet_names:
                print(f"-- Skipping duplicate sheet name in combinations: {sheet_name}")
                continue

            processed_sheet_names.add(sheet_name)

            print(f"-- Processing sheet: {sheet_name}")

            try:
                if sheet_name in existing_sheets:
                    sheet = wb.sheets[sheet_name]
                    sheet.clear()
                    print(f"-- Cleared existing sheet: {sheet_name}")
                else:
                    sheet = wb.sheets.add(sheet_name)
                    print(f"-- Created new sheet: {sheet_name}")

                matching_beams = get_beams_for_criteria(beam_groups, combo)

                if matching_beams:
                    print(f"-- Found {len(matching_beams)} beams for criteria {sheet_name}")

                    beams_by_group = {}
                    for beam_item in matching_beams:
                        group_id = beam_item["group_id"]
                        if group_id not in beams_by_group:
                            beams_by_group[group_id] = []
                        beams_by_group[group_id].append(beam_item)

                    # Process groups and get beam positions
                    sheet_beam_positions = process_group_layout(sheet, template_wb, beams_by_group, combo)

                    # Add positions from this sheet to the main collection
                    if sheet_beam_positions:
                        all_beam_positions.update(sheet_beam_positions)

                else:
                    print(f"-- No beams found for criteria {sheet_name}")

            except Exception as e:
                print(f"⮽⮽ Error processing sheet {sheet_name}: {e}")
                import traceback
                traceback.print_exc()

        # Save the workbook
        wb.save()
        print("-- Structured Excel layout created and saved successfully")

        # Update database with Excel positions
        if all_beam_positions:
            print(f"-- Updating database with {len(all_beam_positions)} beam positions")
            update_beam_positions_in_database(all_beam_positions, db_path)
        else:
            print("-- No beam positions to update in database")

        return True

    except Exception as e:
        print(f"⮽⮽ Error in create_structured_excel_layout: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # Clean up
        if wb is not None:
            try:
                wb.save()
                wb.close()
            except:
                pass
        if template_wb is not None:
            try:
                template_wb.close()
            except:
                pass
        if app is not None:
            try:
                app.quit()
            except:
                pass


def process_group_layout(sheet, template_sheet, beams_by_group, combo):
    """Processes beam groups and creates the structured layout, returns beam positions"""
    beam_positions = {}  # Dicționar pentru a stoca pozițiile grinzilor

    try:
        # Start position for first group
        start_row = 1
        group_vertical_offset = 54  # Each group offset down by 54 cells

        # Get template sheet
        template_sheet = get_template_sheet(template_sheet)

        # Get all groups and sort them by group_id
        sorted_groups = sorted(beams_by_group.items(), key=lambda x: x[0])

        for group_index, (group_id, beams) in enumerate(sorted_groups):
            current_row = start_row + (group_index * group_vertical_offset)

            print(f"-- Processing group {group_id} at row {current_row} with {len(beams)} beams")

            # Process each beam in the group and capture positions
            group_beam_positions = process_beams_in_group(
                sheet, template_sheet, beams, current_row, group_id, combo
            )

            # Adaugă pozițiile din acest grup la dicționarul principal
            beam_positions.update(group_beam_positions)

            # Add group separator or information
            add_group_info(sheet, current_row, group_id, combo, len(beams))

        return beam_positions

    except Exception as e:
        print(f"⮽⮽ Error in process_group_layout: {e}")
        import traceback
        traceback.print_exc()
        return beam_positions


def process_beams_in_group(sheet, template_sheet, beams, start_row, group_id, combo):
    """Processes individual beams and returns their Excel positions"""
    beam_positions = {}
    horizontal_offset = 40

    print(f"-- Processing {len(beams)} beams in group {group_id} starting at row {start_row}")

    for beam_index, beam_item in enumerate(beams):
        beam = beam_item["beam_data"]
        settings = beam_item["settings"]
        unique_name = beam["unique_name"]

        if beam_index == 0:
            # First beam in group - copy range A1:BC53
            base_col = 1  # Column A
            print(f"-- Copying FULL range A1:BC53 for beam 1 (Group {group_id}) to A{start_row}")

            source_range = template_sheet.range('A1:BC53')
            dest_range = sheet.range(f'A{start_row}')
            copy_range_with_column_widths(source_range, dest_range)

            print(f"-- Successfully copied full range to A{start_row}")

        else:
            # Second and further beams - copy range P1:BC53
            offset_columns = (beam_index * horizontal_offset)
            dest_col = 16 + offset_columns  # P is column 16
            dest_col_letter = number_to_column(dest_col)

            print(f"-- Copying PARTIAL range P1:BC53 for beam {beam_index + 1} (Group {group_id}) to {dest_col_letter}{start_row}")

            source_range = template_sheet.range('P1:BC53')
            dest_range = sheet.range(f'{dest_col_letter}{start_row}')
            copy_range_with_column_widths(source_range, dest_range)

            print(f"-- Successfully copied partial range to {dest_col_letter}{start_row}")

        # Calculate the actual Excel position for this beam
        if beam_index == 0:
            excel_col = 1  # Column A
            excel_col_letter = "A"
        else:
            excel_col = 16 + (beam_index * horizontal_offset)
            excel_col_letter = number_to_column(excel_col)

        excel_row = start_row

        # Store the position
        beam_positions[unique_name] = {
            'sheet_name': combo['sheet_name'],
            'column': excel_col_letter,
            'row': excel_row,
            'full_reference': f"{excel_col_letter}{excel_row}"
        }

        print(f"-- Beam {unique_name} positioned at {excel_col_letter}{excel_row}")

        # Populate beam data in the copied cells
        populate_beam_data(sheet, beam, settings, start_row, beam_index, group_id)

    return beam_positions


def copy_range_with_column_widths(source_range, dest_range):
    """
    Copies a range from source to destination while preserving column widths.
    This ensures the copied template maintains the same column sizing as the original.
    """
    try:
        # First, copy the entire range (values, formatting, formulas, etc.)
        source_range.copy(dest_range)

        # Now copy column widths from source to destination
        copy_column_widths(source_range, dest_range)

        print("-- Copied range with column widths preserved")

    except Exception as e:
        print(f"⮽⮽ Error in copy_range_with_column_widths: {e}")
        # Fallback to simple copy if column width copying fails
        source_range.copy(dest_range)


def copy_column_widths(source_range, dest_range):
    """
    Copies column widths from source range to destination range.
    This ensures the visual layout is preserved.
    """
    try:
        # Get the source worksheet and destination worksheet
        source_sheet = source_range.sheet
        dest_sheet = dest_range.sheet

        # Calculate the column range to copy
        source_start_col = source_range.column
        source_end_col = source_range.column + source_range.columns.count - 1
        dest_start_col = dest_range.column

        # Copy each column width
        for col_offset in range(source_range.columns.count):
            source_col = source_start_col + col_offset
            dest_col = dest_start_col + col_offset

            try:
                # Get column width from source
                source_col_width = source_sheet.range((1, source_col)).column_width

                # Set column width in destination
                dest_sheet.range((1, dest_col)).column_width = source_col_width

            except Exception as col_error:
                print(f"⮽⮽ Warning: Could not copy width for column {source_col} -> {dest_col}: {col_error}")
                # Continue with other columns even if one fails

        print(f"-- Copied column widths for {source_range.columns.count} columns")

    except Exception as e:
        print(f"⮽⮽ Error in copy_column_widths: {e}")
        # Don't let column width errors break the entire process


def copy_excel_file_with_column_widths(source_excel_path, destination_excel_path):
    """Creează o copie a unui fișier Excel folosind xlwings, păstrând toate formatările"""
    app = None
    source_wb = None
    dest_wb = None

    try:
        print(f"-- Sursa: {source_excel_path}")
        print(f"-- Destinație: {destination_excel_path}")

        # Verifică dacă fișierul sursă există
        if not os.path.exists(source_excel_path):
            print(f"⮽⮽ Fișierul sursă nu există: {source_excel_path}")
            return False

        # Verifică dacă folderul destinație există
        destination_dir = os.path.dirname(destination_excel_path)
        if not os.path.exists(destination_dir):
            print(f"⮽⮽ Folderul destinație nu există: {destination_dir}")
            return False

        # Verifică dacă fișierul destinație există deja
        if os.path.exists(destination_excel_path):
            print(f"-- Fișierul destinație există deja, se suprascrie")
            os.remove(destination_excel_path)

        # Deschide aplicația Excel în background
        app = xw.App(visible=False)
        app.display_alerts = False

        print(f"-- Deschidere workbook-ul sursă")
        # Deschide workbook-ul sursă
        source_wb = app.books.open(source_excel_path)

        print(f"-- Creare workbook nou")
        # Creează un workbook nou
        dest_wb = app.books.add()

        # Copiaza fiecare sheet cu toate formatările
        for source_sheet in source_wb.sheets:
            print(f"-- Copiere sheet: {source_sheet.name}")

            # Creează un sheet nou în workbook-ul destinație
            if source_sheet.name == "Sheet1":
                dest_sheet = dest_wb.sheets[0]  # Folosește primul sheet existent
                dest_sheet.name = "Sheet1"
            else:
                dest_sheet = dest_wb.sheets.add(source_sheet.name)

            # Copiaza întregul conținut al sheet-ului
            source_sheet.used_range.copy(dest_sheet.range('A1'))

            # Copiaza lățimile coloanelor
            copy_all_column_widths(source_sheet, dest_sheet)

            # Copiaza înălțimile rândurilor
            copy_all_row_heights(source_sheet, dest_sheet)

        print(f"-- Salvare ca fișier nou")
        # Salvează ca fișier nou la locația specificată
        dest_wb.save(destination_excel_path)

        print(f"-- Închidere workbook-uri")
        # Închide workbook-urile
        source_wb.close()
        dest_wb.close()

        # Verifică dacă copia a fost creată
        if os.path.exists(destination_excel_path):
            file_size = os.path.getsize(destination_excel_path)
            print(f"✓✓ Fișier Excel copiat cu succes: {destination_excel_path}")
            print(f"-- Dimensiune fișier: {file_size} bytes")
            return True
        else:
            print(f"⮽⮽ Eroare - fișierul destinație nu a fost creat")
            return False

    except Exception as e:
        print(f"⮽⮽ Eroare la copierea fișierului Excel cu xlwings: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # Clean up
        if source_wb is not None:
            try:
                source_wb.close()
            except:
                pass
        if dest_wb is not None:
            try:
                dest_wb.close()
            except:
                pass
        if app is not None:
            try:
                app.quit()
            except:
                pass


def copy_all_column_widths(source_sheet, dest_sheet):
    """Copiază toate lățimile coloanelor de la sursă la destinație"""
    try:
        # Obține numărul de coloane utilizate
        last_col = source_sheet.range('XFD1').end('left').column

        for col in range(1, last_col + 1):
            try:
                col_width = source_sheet.range((1, col)).column_width
                dest_sheet.range((1, col)).column_width = col_width
            except Exception as e:
                # Continuă cu următoarea coloană dacă apare o eroare
                continue

        print(f"-- Copied column widths for {last_col} columns")

    except Exception as e:
        print(f"⮽⮽ Error copying all column widths: {e}")


def copy_all_row_heights(source_sheet, dest_sheet):
    """Copiază toate înălțimile rândurilor de la sursă la destinație"""
    try:
        # Obține numărul de rânduri utilizate
        last_row = source_sheet.range('A1048576').end('up').row

        for row in range(1, last_row + 1):
            try:
                row_height = source_sheet.range((row, 1)).row_height
                dest_sheet.range((row, 1)).row_height = row_height
            except Exception as e:
                # Continuă cu următorul rând dacă apare o eroare
                continue

        print(f"-- Copied row heights for {last_row} rows")

    except Exception as e:
        print(f"⮽⮽ Error copying all row heights: {e}")


def populate_beam_data(sheet, beam, settings, start_row, beam_index, group_id):
    """Populates beam-specific data in the copied cell ranges"""
    try:
        # Calculate the horizontal position based on beam index
        if beam_index == 0:
            # First beam - starts at column A
            base_col = 1  # Column A
        else:
            # Subsequent beams - offset by 40 columns each time (changed from 41)
            base_col = 1 + (beam_index * 40)  # Starting from column P (16) but relative to template

        print(
            f"-- Populating beam data for beam {beam_index + 1} in group {group_id} at row {start_row}, base column {base_col}")

        # Define where to put beam information (adjust these coordinates based on your template)
        # These are relative positions within the copied template range
        beam_data_positions = {
            'beam_label': (1, 2),  # Row 1, Column B within the copied range
            'beam_id': (1, 5),  # Row 1, Column E within the copied range
            'group_id': (2, 2),  # Row 2, Column B within the copied range
            'scenario': (2, 5),  # Row 2, Column E within the copied range
            'story': (3, 2),  # Row 3, Column B within the copied range
            'section': (3, 5),  # Row 3, Column E within the copied range
        }

        # Get beam properties from ETABS
        try:
            from etabs_api.operations import get_label_and_story, get_section_name, get_section_material, \
                get_frame_length

            label, story = get_label_and_story(beam['unique_name'])
            section_name = get_section_name(beam['unique_name'])
            material = get_section_material(beam['unique_name'])
            length = get_frame_length(beam['unique_name'])

            print(
                f"-- Beam data: Label={label}, Story={story}, Section={section_name}, Material={material}, Length={length}")

        except Exception as e:
            print(f"⮽⮽ Error getting beam properties: {e}")
            label, story, section_name, material, length = "N/A", "N/A", "N/A", "N/A", 0.0

        # Populate the data in the actual cells
        for field, (row_offset, col_offset) in beam_data_positions.items():
            # Calculate absolute cell position
            absolute_row = start_row + row_offset - 1  # -1 because Excel is 1-based but our offsets are 1-based
            absolute_col = base_col + col_offset - 1  # -1 for same reason

            cell = sheet.range(absolute_row, absolute_col)

            if field == 'beam_label':
                cell.value = label or beam.get('label', 'N/A')
            elif field == 'beam_id':
                cell.value = beam_index + 1
            elif field == 'group_id':
                cell.value = group_id
            elif field == 'scenario':
                scenario_value = "A" if settings.get('scenario') == "A" else "B"
                cell.value = "Infrastructura" if scenario_value == "A" else "Suprastructura"
            elif field == 'story':
                cell.value = story or settings.get('etaj', 'N/A')
            elif field == 'section':
                cell.value = section_name

        print(f"-- Successfully populated beam data for beam {beam_index + 1}")

    except Exception as e:
        print(f"⮽⮽ Error populating beam data: {e}")
        import traceback
        traceback.print_exc()


def populate_design_parameters(sheet, settings, start_cell):
    """Populates design parameters in the template"""
    try:
        # Define positions for design parameters (adjust based on your template)
        design_positions = {
            'rezistente': (6, 2),  # Row 6, Column B
            'dcl': (7, 2),  # Row 7, Column B
            'dcm': (7, 4),  # Row 7, Column D
            'dch': (7, 6),  # Row 7, Column F
            'secundare': (8, 2),  # Row 8, Column B
            'dir_x': (8, 4),  # Row 8, Column D
            'dir_y': (8, 6),  # Row 8, Column F
            'comb_upper': (9, 2),  # Row 9, Column B
            'comb_lower': (10, 2),  # Row 10, Column B
        }

        for param, (row_offset, col_offset) in design_positions.items():
            cell = start_cell.offset(row_offset - 1, col_offset - 1)

            if param in settings:
                value = settings[param]
                if isinstance(value, bool):
                    cell.value = "✓" if value else "✗"
                else:
                    cell.value = value

    except Exception as e:
        print(f"⮽⮽ Error populating design parameters: {e}")


def add_group_info(sheet, start_row, group_id, combo, beam_count):
    """Adds group information and formatting"""
    try:
        # Add group header above the beam data (2 rows above the start)
        header_row = max(1, start_row - 2)  # Ensure we don't go below row 1

        # Add group header in column A
        header_cell = sheet.range(f'A{header_row}')
        header_cell.value = f"Group {group_id} - {combo['sheet_name']} - {beam_count} beams"
        header_cell.font.bold = True
        header_cell.font.size = 12
        # Use a simpler approach for background color
        try:
            header_cell.color = (200, 200, 255)  # Light blue background
        except:
            pass  # Skip color if it causes issues

        print(f"-- Added group header for group {group_id} at row {header_row}")

    except Exception as e:
        print(f"⮽⮽ Error adding group info: {e}")
        # Don't let group header errors stop the process


def number_to_column(n):
    """Convert column number to Excel column letter (1->A, 2->B, ..., 27->AA, etc.)"""
    result = ""
    while n > 0:
        n, remainder = divmod(n - 1, 26)
        result = chr(65 + remainder) + result
    return result


def get_sheet_combinations(beam_groups):
    """
    Extracts all unique combinations of criteria for sheet creation.
    Returns a list of dictionaries with sheet criteria.
    """
    combinations_dict = {}  # Use dict to ensure uniqueness by sheet name

    for group in beam_groups.get("groups", []):
        settings = group.get("settings", {})

        # Extract criteria (handle None values)
        story = settings.get("etaj", "Unknown")
        if story is None:
            story = "Unknown"

        scenario = group.get("scenario", "Unknown")
        dir_x = settings.get("dir_x", "False").lower() == "true"
        dir_y = settings.get("dir_y", "False").lower() == "true"
        secondary = settings.get("secundare", "False").lower() == "true"

        # Determine direction
        if secondary:
            direction = "Secondary"
        elif dir_x and dir_y:
            direction = "Both"
        elif dir_x:
            direction = "DirX"
        elif dir_y:
            direction = "DirY"
        else:
            direction = "NoDirection"

        # Generate sheet name
        sheet_name = generate_sheet_name(story, scenario, direction, secondary)

        # Use sheet name as key to ensure uniqueness
        if sheet_name not in combinations_dict:
            combinations_dict[sheet_name] = {
                "story": story,
                "scenario": scenario,
                "direction": direction,
                "secondary": secondary,
                "sheet_name": sheet_name
            }

    # Convert to list
    sheet_combinations = list(combinations_dict.values())
    print(f"-- Generated {len(sheet_combinations)} unique sheet combinations")

    # Debug: print all sheet names
    for combo in sheet_combinations:
        print(f"   - {combo['sheet_name']}")

    return sheet_combinations


def generate_sheet_name(story, scenario, direction, secondary):
    """Generates a sheet name based on criteria with shorter names for Excel compatibility"""
    parts = []

    # Add scenario (shorter versions)
    if scenario == "A":
        parts.append("Infr")  # Shorter for Infrastructura
    elif scenario == "B":
        parts.append("Supr")  # Shorter for Suprastructura
    else:
        parts.append(scenario[:4])  # Limit to 4 chars for other scenarios

    # Add story (handle None values and simplify name)
    if story is None:
        story_simple = "Unknown"
    else:
        # Extract only the essential part of the story name
        story_simple = story.split(' - ')[0] if ' - ' in story else story
        # Remove any special characters and limit length
        story_simple = ''.join(c for c in story_simple if c.isalnum() or c in [' ', '-'])
        story_simple = story_simple.replace(' ', '')  # Remove spaces to be more compact
        story_simple = story_simple[:10]  # Limit to 10 characters

    parts.append(story_simple)

    # Add direction (shorter versions)
    if secondary:
        parts.append("Sec")
    else:
        if direction == "Both":
            parts.append("XY")
        elif direction == "DirX":
            parts.append("X")
        elif direction == "DirY":
            parts.append("Y")
        elif direction == "NoDirection":
            parts.append("NoDir")
        else:
            parts.append(direction[:3])  # Limit to 3 chars for other directions

    sheet_name = "-".join(parts)  # Use hyphens instead of " - " to save space

    # Excel sheet names max 31 characters - ensure we're within limit
    if len(sheet_name) > 31:
        # Make story name even shorter
        parts[1] = parts[1][:6]  # Limit story to 6 chars
        sheet_name = "-".join(parts)

    # Final safety check - truncate if still too long
    if len(sheet_name) > 31:
        sheet_name = sheet_name[:31]

    return sheet_name


def get_beams_for_criteria(beam_groups, combo):
    """Filters beams that match the specific criteria"""
    matching_beams = []

    for group in beam_groups.get("groups", []):
        group_settings = group.get("settings", {})

        # Check if group matches the sheet criteria
        if matches_criteria(group, group_settings, combo):
            for beam in group.get("beams", []):
                matching_beams.append({
                    "group_id": group.get("group_id", 1),
                    "beam_data": beam,
                    "settings": group_settings
                })

    return matching_beams


def matches_criteria(group, group_settings, combo):
    """Checks if a beam group matches the sheet criteria"""
    try:
        # Check story (handle None values)
        group_story = group_settings.get("etaj", "Unknown")
        if group_story is None:
            group_story = "Unknown"

        story_match = group_story == combo["story"]

        # Check scenario
        scenario_match = group.get("scenario", "Unknown") == combo["scenario"]

        # Check direction and secondary
        dir_x = group_settings.get("dir_x", "False").lower() == "true"
        dir_y = group_settings.get("dir_y", "False").lower() == "true"
        secondary = group_settings.get("secundare", "False").lower() == "true"

        if secondary:
            direction_match = combo["secondary"] == True and combo["direction"] == "Secondary"
        else:
            if dir_x and dir_y:
                direction_match = combo["direction"] == "Both"
            elif dir_x:
                direction_match = combo["direction"] == "DirX"
            elif dir_y:
                direction_match = combo["direction"] == "DirY"
            else:
                direction_match = combo["direction"] == "NoDirection"

        return story_match and scenario_match and direction_match

    except Exception as e:
        print(f"⮽⮽ Error in matches_criteria: {e}")
        return False


# Update the main create_dynamic_excel_sheets function to use the new structured layout
def create_dynamic_excel_sheets(excel_path, db_path="frames.db", template_excel_path=None):
    """
    Creates Excel with dynamic sheets using structured layout.
    This replaces the old dynamic sheet creation.
    """
    if template_excel_path is None:
        # Try to get template path from the main application
        print("⮽⮽ No template path provided for structured layout")
        return False

    return create_structured_excel_layout(excel_path, template_excel_path, db_path)


def update_database_with_excel_positions(db_path="frames.db"):
    """Actualizează baza de date cu pozițiile Excel pentru fiecare grindă"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Verifică dacă coloanele există deja (pentru compatibilitate)
        cursor.execute("PRAGMA table_info(Frames)")
        columns = [column[1] for column in cursor.fetchall()]

        if 'ExcelColumn' not in columns:
            print("-- Adăugare coloane Excel în baza de date...")
            cursor.execute("ALTER TABLE Frames ADD COLUMN ExcelColumn TEXT")
            cursor.execute("ALTER TABLE Frames ADD COLUMN ExcelRow INTEGER")
            cursor.execute("ALTER TABLE Frames ADD COLUMN SheetName TEXT")

        conn.commit()
        conn.close()
        print("-- Baza de date este pregătită pentru pozițiile Excel")
        return True

    except Exception as e:
        print(f"⮽⮽ Eroare la pregătirea bazei de date pentru pozițiile Excel: {e}")
        return False


def update_beam_positions_in_database(beam_positions, db_path="frames.db"):
    """Actualizează baza de date cu pozițiile Excel colectate"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        updated_count = 0
        for unique_name, position in beam_positions.items():
            cursor.execute("""
            UPDATE Frames 
            SET ExcelColumn = ?, ExcelRow = ?, SheetName = ?
            WHERE UniqueName = ?
            """, (
                position['column'],
                position['row'],
                position['sheet_name'],
                unique_name
            ))

            if cursor.rowcount > 0:
                updated_count += 1
                print(
                    f"-- Updated position for {unique_name}: {position['sheet_name']}!{position['column']}{position['row']}")
            else:
                print(f"⮽⮽ Could not find beam {unique_name} in database")

        conn.commit()
        conn.close()
        print(f"-- Successfully updated {updated_count} beam positions in database")
        return True

    except Exception as e:
        print(f"⮽⮽ Error updating beam positions in database: {e}")
        return False


def get_template_sheet(template_wb):
    """Get the template sheet from the workbook"""
    try:
        sheet_names = ['Sheet1', 'Sheet 1', 'Template', 'Sheet1$']
        for sheet_name in sheet_names:
            try:
                template_sheet = template_wb.sheets[sheet_name]
                print(f"-- Found template sheet: {sheet_name}")
                return template_sheet
            except:
                continue

        # If no specific sheet found, use the first sheet
        template_sheet = template_wb.sheets[0]
        print("-- Using first sheet as template")
        return template_sheet

    except Exception as e:
        print(f"⮽⮽ Error getting template sheet: {e}")
        raise