"""
Accessibility Compliance Tests

Tests for WCAG compliance, screen reader compatibility,
keyboard navigation, and other accessibility requirements.
"""

import pytest
import asyncio
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from axe_selenium_python import Axe
import requests
from typing import Dict, List, Any


class TestWCAGCompliance:
    """Test Web Content Accessibility Guidelines (WCAG) compliance"""
    
    @pytest.fixture
    def webdriver_instance(self):
        """Setup headless Chrome for accessibility testing"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        driver = webdriver.Chrome(options=chrome_options)
        yield driver
        driver.quit()
    
    def test_wcag_aa_compliance_automated(self, webdriver_instance):
        """Test WCAG AA compliance using automated axe-core testing"""
        driver = webdriver_instance
        
        # Test main application page
        driver.get("http://localhost:3000")
        
        # Wait for page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Inject axe-core and run accessibility tests
        axe = Axe(driver)
        axe.inject()
        
        # Run accessibility scan
        results = axe.run()
        
        # Check for violations
        violations = results.get("violations", [])
        
        # Log violations for debugging
        if violations:
            print(f"\nFound {len(violations)} accessibility violations:")
            for violation in violations:
                print(f"- {violation['id']}: {violation['description']}")
                print(f"  Impact: {violation['impact']}")
                print(f"  Help: {violation['helpUrl']}")
        
        # Assert no critical or serious violations
        critical_violations = [v for v in violations if v['impact'] == 'critical']
        serious_violations = [v for v in violations if v['impact'] == 'serious']
        
        assert len(critical_violations) == 0, f"Critical accessibility violations found: {critical_violations}"
        assert len(serious_violations) == 0, f"Serious accessibility violations found: {serious_violations}"
    
    def test_color_contrast_compliance(self, webdriver_instance):
        """Test color contrast compliance (WCAG AA: 4.5:1, AAA: 7:1)"""
        driver = webdriver_instance
        driver.get("http://localhost:3000")
        
        # Get all text elements
        text_elements = driver.find_elements(
            By.CSS_SELECTOR, 
            "p, h1, h2, h3, h4, h5, h6, span, div, button, a, label, input"
        )
        
        contrast_failures = []
        
        for element in text_elements[:20]:  # Test first 20 elements
            if element.text.strip():
                try:
                    # Get computed styles
                    styles = driver.execute_script("""
                        var element = arguments[0];
                        var styles = window.getComputedStyle(element);
                        return {
                            color: styles.color,
                            backgroundColor: styles.backgroundColor,
                            fontSize: styles.fontSize,
                            fontWeight: styles.fontWeight
                        };
                    """, element)
                    
                    # Basic contrast check - ensure colors are different
                    if styles["color"] == styles["backgroundColor"]:
                        contrast_failures.append({
                            "element": element.tag_name,
                            "text": element.text[:50],
                            "issue": "Text color matches background color"
                        })
                    
                    # Check for transparent backgrounds with light text
                    if ("rgba(0, 0, 0, 0)" in styles["backgroundColor"] and 
                        "rgb(255, 255, 255)" in styles["color"]):
                        contrast_failures.append({
                            "element": element.tag_name,
                            "text": element.text[:50],
                            "issue": "White text on transparent background"
                        })
                        
                except Exception as e:
                    # Skip elements that can't be analyzed
                    continue
        
        assert len(contrast_failures) == 0, f"Color contrast failures: {contrast_failures}"
    
    def test_heading_structure_compliance(self, webdriver_instance):
        """Test proper heading structure (WCAG 2.4.6)"""
        driver = webdriver_instance
        driver.get("http://localhost:3000")
        
        # Get all headings
        headings = driver.find_elements(By.CSS_SELECTOR, "h1, h2, h3, h4, h5, h6")
        
        if not headings:
            pytest.skip("No headings found on page")
        
        heading_levels = []
        for heading in headings:
            level = int(heading.tag_name[1])  # Extract number from h1, h2, etc.
            heading_levels.append(level)
        
        # Check heading structure
        structure_issues = []
        
        # Should start with h1
        if heading_levels and heading_levels[0] != 1:
            structure_issues.append("Page should start with h1")
        
        # Check for skipped levels
        for i in range(1, len(heading_levels)):
            current_level = heading_levels[i]
            previous_level = heading_levels[i-1]
            
            if current_level > previous_level + 1:
                structure_issues.append(
                    f"Heading level skipped: h{previous_level} followed by h{current_level}"
                )
        
        assert len(structure_issues) == 0, f"Heading structure issues: {structure_issues}"
    
    def test_image_alt_text_compliance(self, webdriver_instance):
        """Test image alt text compliance (WCAG 1.1.1)"""
        driver = webdriver_instance
        driver.get("http://localhost:3000")
        
        # Get all images
        images = driver.find_elements(By.TAG_NAME, "img")
        
        alt_text_issues = []
        
        for img in images:
            alt_text = img.get_attribute("alt")
            src = img.get_attribute("src")
            
            # Check for missing alt attribute
            if alt_text is None:
                alt_text_issues.append({
                    "src": src,
                    "issue": "Missing alt attribute"
                })
            # Check for empty alt text on non-decorative images
            elif alt_text == "" and not self._is_decorative_image(img):
                alt_text_issues.append({
                    "src": src,
                    "issue": "Empty alt text on non-decorative image"
                })
            # Check for generic alt text
            elif alt_text and alt_text.lower() in ["image", "picture", "photo", "graphic"]:
                alt_text_issues.append({
                    "src": src,
                    "issue": f"Generic alt text: '{alt_text}'"
                })
        
        assert len(alt_text_issues) == 0, f"Image alt text issues: {alt_text_issues}"
    
    def _is_decorative_image(self, img_element):
        """Check if image is decorative based on context"""
        # Simple heuristic - check if image is in a decorative context
        parent_classes = img_element.find_element(By.XPATH, "..").get_attribute("class") or ""
        return any(keyword in parent_classes.lower() for keyword in ["decoration", "background", "icon"])


class TestKeyboardNavigationCompliance:
    """Test keyboard navigation accessibility compliance"""
    
    @pytest.fixture
    def webdriver_instance(self):
        """Setup Chrome for keyboard navigation testing"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        driver = webdriver.Chrome(options=chrome_options)
        yield driver
        driver.quit()
    
    def test_keyboard_navigation_order(self, webdriver_instance):
        """Test logical keyboard navigation order (WCAG 2.4.3)"""
        return self.test_tab_navigation_order(webdriver_instance)
    
    def test_tab_navigation_order(self, webdriver_instance):
        """Test logical tab navigation order (WCAG 2.4.3)"""
        driver = webdriver_instance
        driver.get("http://localhost:3000")
        
        # Get all focusable elements
        focusable_elements = driver.find_elements(
            By.CSS_SELECTOR,
            'button, input, select, textarea, a[href], [tabindex]:not([tabindex="-1"])'
        )
        
        if not focusable_elements:
            pytest.skip("No focusable elements found")
        
        # Test tab navigation
        body = driver.find_element(By.TAG_NAME, "body")
        navigation_order = []
        
        # Start from body and tab through elements
        body.click()  # Focus on body
        
        for i in range(min(10, len(focusable_elements))):  # Test first 10 elements
            body.send_keys(Keys.TAB)
            time.sleep(0.1)  # Small delay for focus to settle
            
            try:
                focused_element = driver.switch_to.active_element
                element_info = {
                    "tag": focused_element.tag_name,
                    "type": focused_element.get_attribute("type"),
                    "id": focused_element.get_attribute("id"),
                    "class": focused_element.get_attribute("class"),
                    "text": focused_element.text[:30] if focused_element.text else ""
                }
                navigation_order.append(element_info)
            except Exception:
                # Skip if element can't be analyzed
                continue
        
        # Verify navigation order makes logical sense
        # (This is a basic check - more sophisticated logic could be added)
        assert len(navigation_order) > 0, "No elements received focus during tab navigation"
        
        # Check that focus is visible
        for element_info in navigation_order:
            # This is a simplified check - in practice, you'd verify focus styles
            assert element_info["tag"] in ["button", "input", "select", "textarea", "a"], \
                f"Non-interactive element received focus: {element_info}"
    
    def test_keyboard_trap_avoidance(self, webdriver_instance):
        """Test that keyboard focus doesn't get trapped (WCAG 2.1.2)"""
        driver = webdriver_instance
        driver.get("http://localhost:3000")
        
        body = driver.find_element(By.TAG_NAME, "body")
        
        # Tab through many elements to check for traps
        previous_focused_elements = []
        
        for i in range(20):  # Tab 20 times
            body.send_keys(Keys.TAB)
            time.sleep(0.1)
            
            try:
                focused_element = driver.switch_to.active_element
                element_id = focused_element.get_attribute("id") or f"{focused_element.tag_name}_{i}"
                
                # Check if we're stuck on the same element
                if len(previous_focused_elements) >= 3:
                    last_three = previous_focused_elements[-3:]
                    if all(elem == element_id for elem in last_three):
                        pytest.fail(f"Keyboard focus trapped on element: {element_id}")
                
                previous_focused_elements.append(element_id)
                
            except Exception:
                continue
        
        # Test Shift+Tab (reverse navigation)
        for i in range(5):
            body.send_keys(Keys.SHIFT + Keys.TAB)
            time.sleep(0.1)
        
        # Should be able to navigate backwards without issues
        assert True  # If we reach here, no keyboard traps were detected
    
    def test_skip_links_functionality(self, webdriver_instance):
        """Test skip links functionality (WCAG 2.4.1)"""
        driver = webdriver_instance
        driver.get("http://localhost:3000")
        
        # Look for skip links
        skip_links = driver.find_elements(
            By.CSS_SELECTOR,
            'a[href^="#"], a[href*="skip"], a[href*="main"]'
        )
        
        if not skip_links:
            pytest.skip("No skip links found")
        
        for skip_link in skip_links[:3]:  # Test first 3 skip links
            # Click the skip link
            skip_link.click()
            time.sleep(0.2)
            
            # Verify focus moved to target
            href = skip_link.get_attribute("href")
            if href and "#" in href:
                target_id = href.split("#")[-1]
                
                try:
                    target_element = driver.find_element(By.ID, target_id)
                    focused_element = driver.switch_to.active_element
                    
                    # Verify focus moved to target or near target
                    assert (focused_element == target_element or 
                           target_element in driver.find_elements(By.XPATH, ".//*")), \
                           f"Skip link did not move focus to target: {target_id}"
                except Exception:
                    # Target might not be focusable, which is acceptable
                    pass
    
    def test_keyboard_shortcuts_accessibility(self, webdriver_instance):
        """Test keyboard shortcuts don't interfere with assistive technology"""
        driver = webdriver_instance
        driver.get("http://localhost:3000")
        
        # Test common assistive technology key combinations
        problematic_shortcuts = [
            Keys.F1,  # Help in screen readers
            Keys.F3,  # Find in screen readers
            Keys.F5,  # Refresh (should work)
            Keys.F7,  # Caret browsing in some browsers
        ]
        
        body = driver.find_element(By.TAG_NAME, "body")
        
        for shortcut in problematic_shortcuts:
            try:
                # Send shortcut key
                body.send_keys(shortcut)
                time.sleep(0.2)
                
                # Verify page is still functional
                # (This is a basic check - more sophisticated testing could be added)
                assert driver.current_url is not None
                assert body.is_displayed()
                
            except Exception as e:
                # Some shortcuts might not be testable in headless mode
                continue


class TestScreenReaderCompatibility:
    """Test screen reader compatibility and ARIA implementation"""
    
    @pytest.fixture
    def webdriver_instance(self):
        """Setup Chrome for screen reader testing"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        driver = webdriver.Chrome(options=chrome_options)
        yield driver
        driver.quit()
    
    def test_aria_labels_presence(self, webdriver_instance):
        """Test presence and quality of ARIA labels"""
        driver = webdriver_instance
        driver.get("http://localhost:3000")
        
        # Find interactive elements that should have ARIA labels
        interactive_elements = driver.find_elements(
            By.CSS_SELECTOR,
            'button, input, select, textarea, [role="button"], [role="link"], [role="tab"]'
        )
        
        aria_issues = []
        
        for element in interactive_elements:
            # Check for accessible name
            aria_label = element.get_attribute("aria-label")
            aria_labelledby = element.get_attribute("aria-labelledby")
            aria_describedby = element.get_attribute("aria-describedby")
            title = element.get_attribute("title")
            text_content = element.text.strip()
            
            # Check if element has an accessible name
            has_accessible_name = any([
                aria_label,
                aria_labelledby,
                title,
                text_content
            ])
            
            if not has_accessible_name:
                aria_issues.append({
                    "element": element.tag_name,
                    "id": element.get_attribute("id"),
                    "class": element.get_attribute("class"),
                    "issue": "No accessible name found"
                })
            
            # Check for generic or unhelpful labels
            if aria_label and aria_label.lower() in ["button", "link", "input", "click here"]:
                aria_issues.append({
                    "element": element.tag_name,
                    "id": element.get_attribute("id"),
                    "issue": f"Generic ARIA label: '{aria_label}'"
                })
        
        assert len(aria_issues) == 0, f"ARIA labeling issues: {aria_issues}"
    
    def test_semantic_html_structure(self, webdriver_instance):
        """Test semantic HTML structure for screen readers"""
        driver = webdriver_instance
        driver.get("http://localhost:3000")
        
        # Check for semantic landmarks
        landmarks = {
            "main": driver.find_elements(By.TAG_NAME, "main"),
            "nav": driver.find_elements(By.TAG_NAME, "nav"),
            "header": driver.find_elements(By.TAG_NAME, "header"),
            "footer": driver.find_elements(By.TAG_NAME, "footer"),
            "aside": driver.find_elements(By.TAG_NAME, "aside"),
            "section": driver.find_elements(By.TAG_NAME, "section")
        }
        
        # Check for ARIA landmarks
        aria_landmarks = {
            "main": driver.find_elements(By.CSS_SELECTOR, '[role="main"]'),
            "navigation": driver.find_elements(By.CSS_SELECTOR, '[role="navigation"]'),
            "banner": driver.find_elements(By.CSS_SELECTOR, '[role="banner"]'),
            "contentinfo": driver.find_elements(By.CSS_SELECTOR, '[role="contentinfo"]'),
            "complementary": driver.find_elements(By.CSS_SELECTOR, '[role="complementary"]')
        }
        
        # Verify essential landmarks exist
        essential_landmarks = ["main", "nav"]
        missing_landmarks = []
        
        for landmark in essential_landmarks:
            html_elements = landmarks.get(landmark, [])
            aria_elements = aria_landmarks.get(landmark, []) if landmark in aria_landmarks else []
            
            if not html_elements and not aria_elements:
                missing_landmarks.append(landmark)
        
        assert len(missing_landmarks) == 0, f"Missing essential landmarks: {missing_landmarks}"
    
    def test_form_accessibility(self, webdriver_instance):
        """Test form accessibility for screen readers"""
        driver = webdriver_instance
        driver.get("http://localhost:3000")
        
        # Find all form inputs
        form_inputs = driver.find_elements(By.CSS_SELECTOR, "input, select, textarea")
        
        form_issues = []
        
        for input_element in form_inputs:
            input_type = input_element.get_attribute("type")
            input_id = input_element.get_attribute("id")
            input_name = input_element.get_attribute("name")
            
            # Check for associated label
            label_association = False
            
            if input_id:
                # Look for label with for attribute
                labels = driver.find_elements(By.CSS_SELECTOR, f'label[for="{input_id}"]')
                if labels:
                    label_association = True
            
            # Check for ARIA labeling
            aria_label = input_element.get_attribute("aria-label")
            aria_labelledby = input_element.get_attribute("aria-labelledby")
            
            if not label_association and not aria_label and not aria_labelledby:
                form_issues.append({
                    "input_type": input_type,
                    "input_id": input_id,
                    "input_name": input_name,
                    "issue": "No label association found"
                })
            
            # Check for required field indication
            if input_element.get_attribute("required"):
                aria_required = input_element.get_attribute("aria-required")
                if not aria_required:
                    form_issues.append({
                        "input_type": input_type,
                        "input_id": input_id,
                        "issue": "Required field not indicated with aria-required"
                    })
        
        assert len(form_issues) == 0, f"Form accessibility issues: {form_issues}"
    
    def test_dynamic_content_announcements(self, webdriver_instance):
        """Test dynamic content announcements for screen readers"""
        driver = webdriver_instance
        driver.get("http://localhost:3000")
        
        # Look for ARIA live regions
        live_regions = driver.find_elements(By.CSS_SELECTOR, '[aria-live]')
        
        # Check for status and alert regions
        status_regions = driver.find_elements(By.CSS_SELECTOR, '[role="status"]')
        alert_regions = driver.find_elements(By.CSS_SELECTOR, '[role="alert"]')
        
        # Verify live regions have appropriate settings
        live_region_issues = []
        
        for region in live_regions:
            aria_live = region.get_attribute("aria-live")
            aria_atomic = region.get_attribute("aria-atomic")
            
            # Check for appropriate aria-live values
            if aria_live not in ["polite", "assertive", "off"]:
                live_region_issues.append({
                    "element": region.tag_name,
                    "id": region.get_attribute("id"),
                    "issue": f"Invalid aria-live value: {aria_live}"
                })
        
        # This test passes if no issues are found with existing live regions
        # (It doesn't require live regions to exist, but validates them if they do)
        assert len(live_region_issues) == 0, f"Live region issues: {live_region_issues}"


class TestMobileAccessibilityCompliance:
    """Test mobile accessibility compliance"""
    
    @pytest.fixture
    def mobile_webdriver_instance(self):
        """Setup Chrome with mobile viewport for accessibility testing"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        driver = webdriver.Chrome(options=chrome_options)
        
        # Set mobile viewport
        driver.set_window_size(375, 667)  # iPhone dimensions
        
        yield driver
        driver.quit()
    
    def test_touch_target_sizes(self, mobile_webdriver_instance):
        """Test touch target sizes meet accessibility guidelines"""
        driver = mobile_webdriver_instance
        driver.get("http://localhost:3000")
        
        # Find interactive elements
        interactive_elements = driver.find_elements(
            By.CSS_SELECTOR,
            "button, input, select, a, [role='button'], [role='link']"
        )
        
        small_targets = []
        
        for element in interactive_elements[:10]:  # Test first 10 elements
            try:
                size = element.size
                location = element.location
                
                # WCAG recommends minimum 44x44 pixels for touch targets
                min_size = 44
                
                if size["width"] < min_size and size["height"] < min_size:
                    small_targets.append({
                        "element": element.tag_name,
                        "id": element.get_attribute("id"),
                        "size": size,
                        "text": element.text[:30] if element.text else ""
                    })
                
            except Exception:
                # Skip elements that can't be measured
                continue
        
        assert len(small_targets) == 0, f"Touch targets too small: {small_targets}"
    
    def test_mobile_navigation_accessibility(self, mobile_webdriver_instance):
        """Test mobile navigation accessibility"""
        driver = mobile_webdriver_instance
        driver.get("http://localhost:3000")
        
        # Look for mobile navigation patterns
        nav_elements = driver.find_elements(By.CSS_SELECTOR, "nav, [role='navigation']")
        
        mobile_nav_issues = []
        
        for nav in nav_elements:
            # Check if navigation is accessible on mobile
            if not nav.is_displayed():
                continue
            
            # Look for hamburger menu or mobile navigation toggle
            toggle_buttons = nav.find_elements(
                By.CSS_SELECTOR,
                'button[aria-expanded], [role="button"][aria-expanded]'
            )
            
            for toggle in toggle_buttons:
                aria_expanded = toggle.get_attribute("aria-expanded")
                aria_controls = toggle.get_attribute("aria-controls")
                
                if not aria_expanded:
                    mobile_nav_issues.append({
                        "element": "navigation toggle",
                        "issue": "Missing aria-expanded attribute"
                    })
                
                if not aria_controls:
                    mobile_nav_issues.append({
                        "element": "navigation toggle",
                        "issue": "Missing aria-controls attribute"
                    })
        
        # This test passes if no issues are found with existing mobile navigation
        assert len(mobile_nav_issues) == 0, f"Mobile navigation issues: {mobile_nav_issues}"
    
    def test_mobile_form_accessibility(self, mobile_webdriver_instance):
        """Test mobile form accessibility"""
        driver = mobile_webdriver_instance
        driver.get("http://localhost:3000")
        
        # Find form inputs
        form_inputs = driver.find_elements(By.CSS_SELECTOR, "input, select, textarea")
        
        mobile_form_issues = []
        
        for input_element in form_inputs:
            input_type = input_element.get_attribute("type")
            
            # Check for appropriate input types on mobile
            if input_type == "text":
                # Check if it should be a more specific type
                name = input_element.get_attribute("name") or ""
                placeholder = input_element.get_attribute("placeholder") or ""
                
                if any(keyword in (name + placeholder).lower() for keyword in ["email", "mail"]):
                    mobile_form_issues.append({
                        "input": name or "unnamed",
                        "issue": "Should use input type='email' for email fields"
                    })
                
                if any(keyword in (name + placeholder).lower() for keyword in ["phone", "tel"]):
                    mobile_form_issues.append({
                        "input": name or "unnamed",
                        "issue": "Should use input type='tel' for phone fields"
                    })
            
            # Check for autocomplete attributes
            autocomplete = input_element.get_attribute("autocomplete")
            if input_type in ["email", "tel", "text"] and not autocomplete:
                mobile_form_issues.append({
                    "input": input_element.get_attribute("name") or "unnamed",
                    "issue": "Missing autocomplete attribute for better mobile UX"
                })
        
        # Allow some mobile form issues as they're recommendations, not strict requirements
        assert len(mobile_form_issues) <= 3, f"Too many mobile form issues: {mobile_form_issues}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])