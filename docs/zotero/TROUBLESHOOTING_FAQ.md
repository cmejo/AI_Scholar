# Zotero Integration Troubleshooting Guide & FAQ

## Table of Contents
1. [Connection Issues](#connection-issues)
2. [Import Problems](#import-problems)
3. [Synchronization Issues](#synchronization-issues)
4. [Search and Display Problems](#search-and-display-problems)
5. [Citation Generation Issues](#citation-generation-issues)
6. [PDF and Attachment Problems](#pdf-and-attachment-problems)
7. [Performance Issues](#performance-issues)
8. [Frequently Asked Questions](#frequently-asked-questions)
9. [Getting Additional Help](#getting-additional-help)

## Connection Issues

### Problem: Cannot Connect to Zotero

**Symptoms:**
- "Connection failed" error message
- Redirect to Zotero fails
- Authorization page doesn't load

**Solutions:**

1. **Check Browser Settings**
   - Disable popup blockers for AI Scholar
   - Clear browser cache and cookies
   - Try a different browser or incognito mode

2. **Verify Zotero Account**
   - Ensure you can log in to zotero.org directly
   - Check if your Zotero account is active
   - Verify you have at least one library

3. **Network Issues**
   - Check your internet connection
   - Try connecting from a different network
   - Contact your IT department if using corporate network

4. **Temporary Service Issues**
   - Check [Zotero Status Page](https://status.zotero.org)
   - Wait 15-30 minutes and try again
   - Contact support if issue persists

### Problem: Connection Keeps Dropping

**Symptoms:**
- Frequent "Please reconnect" messages
- Sync fails with authentication errors
- Connection status shows "Disconnected"

**Solutions:**

1. **Token Refresh Issues**
   - Go to Settings → Integrations → Zotero
   - Click "Reconnect to Zotero"
   - Complete the authorization process again

2. **Account Changes**
   - If you changed your Zotero password, reconnect
   - If you enabled 2FA, you may need to reconnect
   - Check if your Zotero account is still active

3. **Permission Changes**
   - Verify AI Scholar still has necessary permissions
   - Check if you revoked access in Zotero settings
   - Re-authorize with full permissions

### Problem: Group Libraries Not Accessible

**Symptoms:**
- Personal library imports but group libraries don't
- "Permission denied" errors for group content
- Group libraries not listed during import

**Solutions:**

1. **Check Group Membership**
   - Verify you're still a member of the group
   - Check your role in the group (member vs. admin)
   - Ensure the group allows API access

2. **Group Settings**
   - Ask group admin to check API access settings
   - Verify group privacy settings
   - Check if group has been archived or deleted

3. **Re-authorization**
   - Disconnect and reconnect your Zotero account
   - Ensure you grant permissions for group libraries
   - Contact group administrator if issues persist

## Import Problems

### Problem: Import Stuck or Very Slow

**Symptoms:**
- Import progress bar not moving
- "Processing..." message for extended time
- Partial import completion

**Solutions:**

1. **Large Library Handling**
   - Libraries with 5000+ items may take several hours
   - Import continues in background - you can close the browser
   - Check email for completion notification

2. **Network Interruptions**
   - Ensure stable internet connection
   - Avoid switching networks during import
   - Restart import if connection was lost

3. **Force Restart Import**
   - Go to Settings → Integrations → Zotero
   - Click "Reset Import" (this will start over)
   - Contact support before resetting large libraries

### Problem: Missing References After Import

**Symptoms:**
- Reference count doesn't match Zotero
- Specific items missing from AI Scholar
- Collections appear empty

**Solutions:**

1. **Check Import Filters**
   - Verify all item types are enabled for import
   - Check if specific collections were excluded
   - Review import settings and preferences

2. **Zotero Data Issues**
   - Check if items exist in Zotero web library
   - Verify items aren't in Zotero trash
   - Ensure items have required metadata

3. **Sync Status**
   - Check if import is still in progress
   - Look for error messages in import log
   - Try manual sync after import completes

### Problem: Metadata Incomplete or Incorrect

**Symptoms:**
- Missing author names or publication info
- Incorrect publication dates
- Empty abstracts or titles

**Solutions:**

1. **Source Data Quality**
   - Check the same items in Zotero web library
   - Verify metadata quality in original Zotero
   - Update metadata in Zotero, then sync to AI Scholar

2. **Import Mapping Issues**
   - Some Zotero fields may not have AI Scholar equivalents
   - Custom fields might not transfer
   - Contact support for specific mapping issues

3. **Re-import Specific Items**
   - Try manual sync to update specific items
   - Delete and re-import problematic references
   - Check import logs for specific error messages

## Synchronization Issues

### Problem: Sync Not Working

**Symptoms:**
- Changes in Zotero don't appear in AI Scholar
- "Last sync" timestamp not updating
- Sync status shows errors

**Solutions:**

1. **Manual Sync**
   - Go to Settings → Integrations → Zotero
   - Click "Sync Now"
   - Wait for completion and check for errors

2. **Connection Verification**
   - Check if Zotero connection is still active
   - Verify API permissions haven't changed
   - Reconnect if connection status is unclear

3. **Clear Sync Cache**
   - Go to Settings → Advanced → Clear Sync Cache
   - This forces a fresh sync of all data
   - May take longer but resolves most sync issues

### Problem: Sync Conflicts

**Symptoms:**
- Warning messages about conflicting changes
- Items appear duplicated
- Unexpected changes to references

**Solutions:**

1. **Conflict Resolution**
   - AI Scholar uses Zotero as the source of truth
   - Local changes in AI Scholar may be overwritten
   - Export important AI Scholar annotations before sync

2. **Prevent Conflicts**
   - Make metadata changes in Zotero, not AI Scholar
   - Use AI Scholar for analysis, Zotero for management
   - Coordinate with team members on group libraries

### Problem: Slow Sync Performance

**Symptoms:**
- Sync takes much longer than expected
- Frequent timeout errors
- Partial sync completion

**Solutions:**

1. **Network Optimization**
   - Use wired connection instead of WiFi when possible
   - Avoid syncing during peak network usage
   - Close other bandwidth-intensive applications

2. **Library Size Management**
   - Consider syncing smaller collections first
   - Archive old or unused references in Zotero
   - Contact support for very large libraries (10,000+ items)

## Search and Display Problems

### Problem: Search Not Finding Expected Results

**Symptoms:**
- Known references don't appear in search results
- Search returns no results for common terms
- Inconsistent search behavior

**Solutions:**

1. **Search Index Issues**
   - Wait 24 hours after import for full indexing
   - Try different search terms or phrases
   - Use advanced search with specific fields

2. **Search Syntax**
   - Use quotes for exact phrases: "machine learning"
   - Try partial words: "comput*" finds "computer", "computing"
   - Use boolean operators: AND, OR, NOT

3. **Rebuild Search Index**
   - Go to Settings → Advanced → Rebuild Search Index
   - This may take several hours for large libraries
   - Search will be limited during rebuild process

### Problem: References Display Incorrectly

**Symptoms:**
- Formatting issues in reference display
- Missing or garbled text
- Images or special characters not showing

**Solutions:**

1. **Browser Compatibility**
   - Try a different browser (Chrome, Firefox, Safari)
   - Update your browser to the latest version
   - Clear browser cache and reload

2. **Character Encoding**
   - Check if original Zotero data has special characters
   - Some non-Latin characters may display differently
   - Contact support for persistent encoding issues

3. **Display Settings**
   - Check your browser zoom level (100% recommended)
   - Verify display settings in AI Scholar preferences
   - Try different view modes (list, grid, detailed)

## Citation Generation Issues

### Problem: Citations Format Incorrectly

**Symptoms:**
- Missing punctuation or formatting
- Incorrect author name formatting
- Wrong date or publication format

**Solutions:**

1. **Citation Style Verification**
   - Ensure you've selected the correct citation style
   - Try switching styles to see if issue persists
   - Compare with official style guide examples

2. **Source Data Quality**
   - Check if metadata is complete in Zotero
   - Verify author names are properly formatted
   - Ensure publication dates are correct

3. **Style Updates**
   - Citation styles are updated regularly
   - Clear browser cache to get latest style files
   - Contact support for specific style issues

### Problem: Bibliography Export Fails

**Symptoms:**
- Export button doesn't work
- Downloaded file is empty or corrupted
- Export process hangs

**Solutions:**

1. **Browser Issues**
   - Check if downloads are blocked in browser
   - Try right-click "Save As" instead of direct download
   - Use a different browser

2. **Large Bibliography Handling**
   - Try exporting smaller batches (50-100 references)
   - Use different export formats (BibTeX vs. RIS)
   - Contact support for very large bibliographies

3. **Format-Specific Issues**
   - Some formats may not support all reference types
   - Try different export formats
   - Check if specific references cause export failures

## PDF and Attachment Problems

### Problem: PDFs Won't Open or Display

**Symptoms:**
- PDF viewer shows blank page
- "File not found" errors
- PDF loads but content is garbled

**Solutions:**

1. **Browser PDF Support**
   - Ensure browser has PDF viewing enabled
   - Try downloading PDF and opening locally
   - Update browser to latest version

2. **File Integrity**
   - Check if PDF opens correctly in Zotero
   - Verify file isn't corrupted in original source
   - Try re-syncing the specific attachment

3. **Access Permissions**
   - Verify you have permission to access the PDF
   - Check if PDF is behind paywall or access restrictions
   - Ensure Zotero has proper file permissions

### Problem: Annotations Not Syncing

**Symptoms:**
- Highlights made in AI Scholar don't appear in Zotero
- Zotero annotations don't show in AI Scholar
- Annotation sync status shows errors

**Solutions:**

1. **Sync Limitations**
   - Not all annotation types sync between platforms
   - Some Zotero annotation formats aren't supported
   - Check annotation sync settings in preferences

2. **Manual Annotation Sync**
   - Go to specific PDF and click "Sync Annotations"
   - Wait for sync completion before making new annotations
   - Check sync status in PDF viewer

3. **Platform Differences**
   - Annotations may appear differently in each platform
   - Some formatting may not transfer
   - Use consistent annotation tools for best results

## Performance Issues

### Problem: AI Scholar Runs Slowly with Zotero Integration

**Symptoms:**
- Pages load slowly after connecting Zotero
- Search takes much longer than expected
- Browser becomes unresponsive

**Solutions:**

1. **Browser Optimization**
   - Close unnecessary browser tabs
   - Clear browser cache and cookies
   - Restart browser and try again

2. **Library Size Impact**
   - Large libraries (5000+ items) may affect performance
   - Consider using collection filters to limit displayed items
   - Contact support for performance optimization tips

3. **System Resources**
   - Ensure adequate RAM (8GB+ recommended)
   - Close other memory-intensive applications
   - Try using AI Scholar on a more powerful device

### Problem: Import or Sync Uses Too Much Bandwidth

**Symptoms:**
- Internet connection slows during sync
- Data usage warnings from ISP
- Other applications can't connect

**Solutions:**

1. **Bandwidth Management**
   - Schedule syncs during off-peak hours
   - Use sync throttling in advanced settings
   - Pause sync if bandwidth is needed elsewhere

2. **Selective Sync**
   - Sync only essential collections first
   - Exclude large attachments if not needed
   - Use manual sync instead of automatic

## Frequently Asked Questions

### General Questions

**Q: How much does Zotero integration cost?**
A: Zotero integration is included with your AI Scholar subscription. You need a free Zotero account, but no additional Zotero subscription is required.

**Q: Can I use AI Scholar without connecting Zotero?**
A: Yes, AI Scholar works independently. Zotero integration is optional and enhances your research capabilities.

**Q: Will connecting to AI Scholar affect my Zotero library?**
A: No, AI Scholar only reads from your Zotero library. It cannot modify, delete, or add items to your Zotero collection.

**Q: Can I connect multiple Zotero accounts?**
A: Currently, you can connect one Zotero account per AI Scholar account. Contact support if you need to switch accounts.

### Privacy and Security

**Q: Is my Zotero data secure in AI Scholar?**
A: Yes, we use enterprise-grade encryption and security measures. Your data is encrypted in transit and at rest.

**Q: Who can see my imported references?**
A: Only you can see your personal library references. Group library access follows your Zotero group permissions.

**Q: Can I delete my imported Zotero data?**
A: Yes, you can disconnect Zotero integration and choose to delete all imported data from AI Scholar.

**Q: Does AI Scholar store my Zotero password?**
A: No, we use OAuth 2.0 authentication. AI Scholar never sees or stores your Zotero password.

### Technical Questions

**Q: How often does sync happen?**
A: Automatic sync occurs every 4 hours by default. You can adjust this in settings or trigger manual sync anytime.

**Q: What happens if I delete items from Zotero?**
A: Deleted items will be removed from AI Scholar during the next sync. This cannot be undone.

**Q: Can I import references from other reference managers?**
A: Currently, only Zotero is supported. You can import other formats into Zotero first, then sync to AI Scholar.

**Q: Is there a limit to library size?**
A: There's no hard limit, but very large libraries (20,000+ items) may experience slower performance. Contact support for optimization help.

### Feature Questions

**Q: Can I edit reference metadata in AI Scholar?**
A: You can view and search all metadata, but editing should be done in Zotero to maintain sync integrity.

**Q: Do AI-generated insights sync back to Zotero?**
A: AI insights are stored in AI Scholar only. You can export them or add them as notes in Zotero manually.

**Q: Can I share AI Scholar insights with non-users?**
A: Yes, you can export insights, citations, and bibliographies to share with anyone.

**Q: Will my Zotero tags appear in AI Scholar?**
A: Yes, all Zotero tags are imported and can be used for filtering and searching in AI Scholar.

## Getting Additional Help

### Self-Service Resources

1. **Video Tutorials**: Check our [Video Tutorial Library](VIDEO_TUTORIALS.md)
2. **User Guide**: Comprehensive [User Guide](USER_GUIDE.md)
3. **Community Forum**: Connect with other users at [community.aischolar.com](https://community.aischolar.com)
4. **Status Page**: Check service status at [status.aischolar.com](https://status.aischolar.com)

### Contact Support

If you can't resolve your issue using this guide:

1. **Live Chat**: Available during business hours (9 AM - 5 PM EST)
2. **Email Support**: support@aischolar.com (response within 24 hours)
3. **Priority Support**: Available for premium subscribers

### When Contacting Support

Please include:

- **Error Messages**: Exact text of any error messages
- **Steps to Reproduce**: What you were doing when the issue occurred
- **Browser Information**: Browser type and version
- **Library Size**: Approximate number of references in your Zotero library
- **Screenshots**: Visual evidence of the issue (if applicable)

### Emergency Issues

For critical issues affecting your research:

- **Email**: urgent@aischolar.com
- **Subject Line**: Include "URGENT - Zotero Integration"
- **Phone**: Emergency support line (premium subscribers only)

---

*This troubleshooting guide is updated regularly based on user feedback and common issues.*
*Last updated: [Current Date]*
*For the latest version, visit: [docs.aischolar.com/zotero/troubleshooting](https://docs.aischolar.com/zotero/troubleshooting)*