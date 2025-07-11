"""
ADU (Accessory Dwelling Unit) specific data extractor.
Focuses on extracting ADU requirements with confidence scoring and source attribution.
"""

import re
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

from bs4 import BeautifulSoup, Tag, NavigableString

logger = logging.getLogger(__name__)


class ADUExtractor:
    """
    Specialized extractor for ADU-related requirements from bylaw documents.
    """
    
    def __init__(self):
        # Keywords that indicate ADU-related content
        self.adu_keywords = [
            'accessory dwelling unit', 'adu', 'secondary suite', 'in-law suite',
            'granny flat', 'carriage house', 'laneway house', 'garden suite',
            'basement suite', 'accessory unit', 'secondary unit', 'ancillary unit'
        ]
        
        # Measurement conversion factors
        self.measurement_conversions = {
            'feet': 0.3048,  # feet to meters
            'ft': 0.3048,
            'foot': 0.3048,
            'inches': 0.0254,  # inches to meters
            'in': 0.0254,
            'inch': 0.0254,
            'square feet': 0.092903,  # sq ft to sq m
            'sq ft': 0.092903,
            'sqft': 0.092903,
            'sf': 0.092903,
            'square meters': 1.0,
            'sq m': 1.0,
            'sqm': 1.0,
            'sm': 1.0,
            'meters': 1.0,
            'm': 1.0,
            'metre': 1.0,
            'acres': 4046.86,  # acres to sq m
            'acre': 4046.86
        }
    
    def extract_adu_requirements(
        self, 
        content: str, 
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Extract ADU requirements from bylaw content.
        
        Args:
            content: HTML content or plain text
            metadata: Document metadata
            
        Returns:
            Dictionary with extracted ADU requirements
        """
        soup = BeautifulSoup(content, 'html.parser') if '<' in content else None
        text = soup.get_text() if soup else content
        
        # Check if content is ADU-related
        if not self._is_adu_content(text):
            return {
                'is_adu_related': False,
                'confidence': 0.0,
                'requirements': {}
            }
        
        extracted = {
            'is_adu_related': True,
            'extracted_at': datetime.utcnow().isoformat(),
            'source_url': metadata.get('url'),
            'requirements': {},
            'confidence_scores': {},
            'source_attributions': {}
        }
        
        # Extract specific requirements
        requirements = [
            ('max_height_m', self._extract_height_requirement),
            ('max_floor_area_sqm', self._extract_floor_area_requirement),
            ('min_lot_size_sqm', self._extract_lot_size_requirement),
            ('front_setback_m', self._extract_setback_requirement, 'front'),
            ('rear_setback_m', self._extract_setback_requirement, 'rear'),
            ('side_setback_m', self._extract_setback_requirement, 'side'),
            ('max_units', self._extract_unit_count),
            ('parking_spaces_required', self._extract_parking_requirement),
            ('owner_occupancy_required', self._extract_owner_occupancy_requirement)
        ]
        
        for req_data in requirements:
            if len(req_data) == 2:
                req_name, extractor_func = req_data
                args = (text, soup)
            else:
                req_name, extractor_func, extra_arg = req_data
                args = (text, soup, extra_arg)
            
            try:
                result = extractor_func(*args)
                if result['value'] is not None:
                    extracted['requirements'][req_name] = result['value']
                    extracted['confidence_scores'][req_name] = result['confidence']
                    extracted['source_attributions'][req_name] = result['source_text']
            except Exception as e:
                logger.error(f"Error extracting {req_name}: {e}")
        
        # Extract other requirements
        extracted['requirements']['other_requirements'] = self._extract_other_requirements(text, soup)
        
        # Calculate overall confidence
        if extracted['confidence_scores']:
            overall_confidence = sum(extracted['confidence_scores'].values()) / len(extracted['confidence_scores'])
            extracted['overall_confidence'] = round(overall_confidence, 2)
        else:
            extracted['overall_confidence'] = 0.0
        
        return extracted
    
    def _is_adu_content(self, text: str) -> bool:
        """Check if content is related to ADUs."""
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in self.adu_keywords)
    
    def _extract_height_requirement(self, text: str, soup: Optional[BeautifulSoup]) -> Dict[str, Any]:
        """Extract maximum height requirement."""
        patterns = [
            r'(?:maximum|max|not exceed)\s+height\s+(?:of\s+)?(\d+(?:\.\d+)?)\s*(feet|ft|meters?|m)\b',
            r'height\s+(?:shall|must|may)\s+not\s+exceed\s+(\d+(?:\.\d+)?)\s*(feet|ft|meters?|m)\b',
            r'(\d+(?:\.\d+)?)\s*(feet|ft|meters?|m)\s+(?:maximum|max)\s+height',
            r'height\s+(?:limit|limitation|restriction)\s+(?:of\s+)?(\d+(?:\.\d+)?)\s*(feet|ft|meters?|m)\b'
        ]
        
        return self._extract_measurement(text, patterns, 'height')
    
    def _extract_floor_area_requirement(self, text: str, soup: Optional[BeautifulSoup]) -> Dict[str, Any]:
        """Extract maximum floor area requirement."""
        patterns = [
            r'(?:maximum|max|not exceed)\s+(?:floor\s+)?(?:area|space|size)\s+(?:of\s+)?(\d+(?:,\d+)?(?:\.\d+)?)\s*(square\s+feet|sq\s*ft|sqft|sf|square\s+meters?|sq\s*m|sqm)\b',
            r'(?:floor\s+)?(?:area|space|size)\s+(?:shall|must|may)\s+not\s+exceed\s+(\d+(?:,\d+)?(?:\.\d+)?)\s*(square\s+feet|sq\s*ft|sqft|sf|square\s+meters?|sq\s*m|sqm)\b',
            r'(\d+(?:,\d+)?(?:\.\d+)?)\s*(square\s+feet|sq\s*ft|sqft|sf|square\s+meters?|sq\s*m|sqm)\s+(?:maximum|max)\s+(?:floor\s+)?(?:area|space|size)'
        ]
        
        return self._extract_measurement(text, patterns, 'floor_area')
    
    def _extract_lot_size_requirement(self, text: str, soup: Optional[BeautifulSoup]) -> Dict[str, Any]:
        """Extract minimum lot size requirement."""
        patterns = [
            r'(?:minimum|min)\s+lot\s+size\s+(?:of\s+)?(\d+(?:,\d+)?(?:\.\d+)?)\s*(square\s+feet|sq\s*ft|sqft|sf|square\s+meters?|sq\s*m|sqm|acres?)\b',
            r'lot\s+size\s+(?:shall|must)\s+(?:be\s+)?(?:at\s+least|minimum\s+of)\s+(\d+(?:,\d+)?(?:\.\d+)?)\s*(square\s+feet|sq\s*ft|sqft|sf|square\s+meters?|sq\s*m|sqm|acres?)\b',
            r'(\d+(?:,\d+)?(?:\.\d+)?)\s*(square\s+feet|sq\s*ft|sqft|sf|square\s+meters?|sq\s*m|sqm|acres?)\s+(?:minimum|min)\s+lot\s+size'
        ]
        
        return self._extract_measurement(text, patterns, 'lot_size')
    
    def _extract_setback_requirement(self, text: str, soup: Optional[BeautifulSoup], setback_type: str) -> Dict[str, Any]:
        """Extract setback requirements (front, rear, side)."""
        patterns = [
            rf'(?:minimum|min)\s+{setback_type}\s+setback\s+(?:of\s+)?(\d+(?:\.\d+)?)\s*(feet|ft|meters?|m)\b',
            rf'{setback_type}\s+setback\s+(?:shall|must)\s+(?:be\s+)?(?:at\s+least|minimum\s+of)\s+(\d+(?:\.\d+)?)\s*(feet|ft|meters?|m)\b',
            rf'(\d+(?:\.\d+)?)\s*(feet|ft|meters?|m)\s+(?:minimum|min)\s+{setback_type}\s+setback',
            rf'{setback_type}\s+yard\s+(?:of\s+)?(?:at\s+least\s+)?(\d+(?:\.\d+)?)\s*(feet|ft|meters?|m)\b'
        ]
        
        return self._extract_measurement(text, patterns, f'{setback_type}_setback')
    
    def _extract_unit_count(self, text: str, soup: Optional[BeautifulSoup]) -> Dict[str, Any]:
        """Extract maximum number of units allowed."""
        patterns = [
            r'(?:maximum|max|not more than|no more than)\s+(?:of\s+)?(\d+)\s+(?:accessory dwelling )?unit[s]?',
            r'(?:one|1)\s+(?:accessory dwelling )?unit\s+(?:per|for each)',
            r'(?:single|one|1)\s+(?:accessory dwelling )?unit\s+(?:shall|may|is)\s+be\s+(?:allowed|permitted)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if 'one' in match.group(0).lower() or '1' in match.group(0):
                    value = 1
                else:
                    value = int(match.group(1))
                
                return {
                    'value': value,
                    'confidence': 0.9,
                    'source_text': match.group(0)
                }
        
        return {'value': None, 'confidence': 0.0, 'source_text': ''}
    
    def _extract_parking_requirement(self, text: str, soup: Optional[BeautifulSoup]) -> Dict[str, Any]:
        """Extract parking space requirements."""
        patterns = [
            r'(?:minimum|min|at least)\s+(\d+)\s+parking\s+space[s]?',
            r'(\d+)\s+parking\s+space[s]?\s+(?:shall|must)\s+be\s+(?:provided|required)',
            r'parking\s+(?:requirement|space[s]?)\s+(?:of\s+)?(\d+)',
            r'(?:one|1)\s+parking\s+space\s+(?:per|for each)\s+(?:accessory dwelling )?unit'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if 'one' in match.group(0).lower():
                    value = 1
                else:
                    value = int(match.group(1))
                
                return {
                    'value': value,
                    'confidence': 0.85,
                    'source_text': match.group(0)
                }
        
        return {'value': None, 'confidence': 0.0, 'source_text': ''}
    
    def _extract_owner_occupancy_requirement(self, text: str, soup: Optional[BeautifulSoup]) -> Dict[str, Any]:
        """Extract owner occupancy requirements."""
        owner_occupancy_patterns = [
            r'owner\s+(?:must\s+)?occup(?:y|ancy)',
            r'owner\s+(?:shall\s+)?resid(?:e|ence)',
            r'owner\s+(?:occupied|occupancy)\s+(?:required|mandatory)',
            r'(?:primary|principal)\s+residence\s+(?:required|mandatory)'
        ]
        
        no_owner_occupancy_patterns = [
            r'no\s+owner\s+occup(?:y|ancy)\s+(?:required|requirement)',
            r'owner\s+occup(?:y|ancy)\s+(?:not\s+)?(?:required|necessary)',
            r'(?:rental|tenant)\s+(?:allowed|permitted)'
        ]
        
        text_lower = text.lower()
        
        # Check for owner occupancy requirement
        for pattern in owner_occupancy_patterns:
            match = re.search(pattern, text_lower)
            if match:
                return {
                    'value': True,
                    'confidence': 0.9,
                    'source_text': match.group(0)
                }
        
        # Check for no owner occupancy requirement
        for pattern in no_owner_occupancy_patterns:
            match = re.search(pattern, text_lower)
            if match:
                return {
                    'value': False,
                    'confidence': 0.85,
                    'source_text': match.group(0)
                }
        
        return {'value': None, 'confidence': 0.0, 'source_text': ''}
    
    def _extract_measurement(self, text: str, patterns: List[str], measurement_type: str) -> Dict[str, Any]:
        """Extract measurement values with unit conversion."""
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                # Extract number and unit
                number_str = match.group(1).replace(',', '')
                unit = match.group(2).lower().strip()
                
                try:
                    value = float(number_str)
                    
                    # Convert to appropriate metric unit
                    if measurement_type in ['height', 'lot_size', 'floor_area'] and 'setback' not in measurement_type:
                        # For areas, use square meter conversion
                        if measurement_type in ['lot_size', 'floor_area']:
                            conversion_factor = self.measurement_conversions.get(unit, 1.0)
                        else:
                            # For linear measurements, use meter conversion
                            conversion_factor = self.measurement_conversions.get(unit, 1.0)
                    else:
                        # For setbacks, use meter conversion
                        conversion_factor = self.measurement_conversions.get(unit, 1.0)
                    
                    converted_value = value * conversion_factor
                    
                    # Determine confidence based on pattern specificity
                    confidence = 0.95 if 'maximum' in pattern or 'minimum' in pattern else 0.85
                    
                    return {
                        'value': round(converted_value, 2),
                        'confidence': confidence,
                        'source_text': match.group(0),
                        'original_value': value,
                        'original_unit': unit
                    }
                    
                except ValueError:
                    continue
        
        return {'value': None, 'confidence': 0.0, 'source_text': ''}
    
    def _extract_other_requirements(self, text: str, soup: Optional[BeautifulSoup]) -> Dict[str, Any]:
        """Extract other ADU requirements that don't fit standard categories."""
        other_requirements = {}
        
        # Design requirements
        design_patterns = [
            r'(?:architectural|design)\s+(?:compatibility|consistency|harmony)',
            r'(?:same|similar|compatible)\s+(?:design|style|appearance)',
            r'(?:match|complement)\s+(?:principal|main|primary)\s+(?:dwelling|building)'
        ]
        
        for pattern in design_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                other_requirements['design_compatibility'] = {
                    'required': True,
                    'source_text': match.group(0)
                }
                break
        
        # Kitchen requirements
        kitchen_patterns = [
            r'(?:full|complete)\s+kitchen\s+(?:required|mandatory)',
            r'kitchen\s+(?:facilities|equipment)\s+(?:required|mandatory)',
            r'(?:cooking|food preparation)\s+(?:facilities|area)'
        ]
        
        for pattern in kitchen_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                other_requirements['kitchen_required'] = {
                    'required': True,
                    'source_text': match.group(0)
                }
                break
        
        # Separate entrance requirements
        entrance_patterns = [
            r'(?:separate|independent|private)\s+(?:entrance|entry)',
            r'(?:direct|exterior)\s+(?:access|entrance|entry)',
            r'no\s+(?:shared|common)\s+(?:entrance|entry)'
        ]
        
        for pattern in entrance_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                other_requirements['separate_entrance'] = {
                    'required': True,
                    'source_text': match.group(0)
                }
                break
        
        # Utility requirements
        utility_patterns = [
            r'(?:separate|independent)\s+(?:utilities|metering)',
            r'(?:individual|separate)\s+(?:water|electrical|gas)\s+(?:meter|connection)',
            r'(?:shared|common)\s+(?:utilities|metering)'
        ]
        
        for pattern in utility_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                separate_required = 'separate' in match.group(0).lower() or 'independent' in match.group(0).lower()
                other_requirements['separate_utilities'] = {
                    'required': separate_required,
                    'source_text': match.group(0)
                }
                break
        
        return other_requirements
    
    def validate_extracted_data(self, extracted: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate extracted data for reasonableness and consistency.
        
        Args:
            extracted: Extracted ADU requirements
            
        Returns:
            Validation results with warnings and corrections
        """
        validation = {
            'is_valid': True,
            'warnings': [],
            'corrections': {}
        }
        
        requirements = extracted.get('requirements', {})
        
        # Validate height (reasonable range: 2-15 meters)
        if height := requirements.get('max_height_m'):
            if height < 2:
                validation['warnings'].append(f"Height {height}m seems too low")
            elif height > 15:
                validation['warnings'].append(f"Height {height}m seems too high")
        
        # Validate floor area (reasonable range: 20-200 sq m)
        if area := requirements.get('max_floor_area_sqm'):
            if area < 20:
                validation['warnings'].append(f"Floor area {area}sqm seems too small")
            elif area > 200:
                validation['warnings'].append(f"Floor area {area}sqm seems too large")
        
        # Validate lot size (should be larger than floor area)
        if (lot_size := requirements.get('min_lot_size_sqm')) and (area := requirements.get('max_floor_area_sqm')):
            if lot_size < area:
                validation['warnings'].append("Lot size is smaller than floor area")
        
        # Validate setbacks (reasonable range: 0.5-10 meters)
        for setback_type in ['front_setback_m', 'rear_setback_m', 'side_setback_m']:
            if setback := requirements.get(setback_type):
                if setback < 0.5:
                    validation['warnings'].append(f"{setback_type} {setback}m seems too small")
                elif setback > 10:
                    validation['warnings'].append(f"{setback_type} {setback}m seems too large")
        
        # Validate unit count (should be reasonable)
        if units := requirements.get('max_units'):
            if units < 1:
                validation['warnings'].append("Unit count less than 1")
            elif units > 5:
                validation['warnings'].append(f"Unit count {units} seems high for ADU")
        
        # Validate parking (should be reasonable)
        if parking := requirements.get('parking_spaces_required'):
            if parking < 0:
                validation['warnings'].append("Negative parking requirement")
            elif parking > 3:
                validation['warnings'].append(f"Parking requirement {parking} seems high")
        
        if validation['warnings']:
            validation['is_valid'] = False
        
        return validation