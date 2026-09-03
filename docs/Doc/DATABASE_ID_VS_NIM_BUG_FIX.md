# Database ID vs NIM Bug Fix - November 20, 2025

## 🐛 Critical Bug: Attendance Not Updating

### Problem

**Symptom**: Face recognition detects students successfully (shown in terminal), but attendance form doesn't update.

**Console Error**:
```
[Attendance] Status select not found for student: 22024151
```

### Root Cause Analysis

**The Mismatch**:

1. **Face Recognition** returns `student_id` = NIM (e.g., "22024151")
2. **HTML Form** uses database auto-increment ID in field names:
   ```html
   <select name="status_{{ student.id }}">  <!-- database ID like 123 -->
   ```
3. **JavaScript** was searching for: `select[name="status_22024151"]`
4. **Actual field name**: `select[name="status_123"]`

**Data Flow**:
```
Backend (Face Recognition)
  ↓ returns student_id: "22024151" (NIM)
  
Frontend JavaScript
  ↓ searches for select[name="status_22024151"]
  
HTML Form
  ✗ has select[name="status_123"] (database ID)
  
Result: ❌ NOT FOUND!
```

### Database Schema

**Students Table**:
```sql
CREATE TABLE students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,  -- Database ID (e.g., 123)
    student_id TEXT UNIQUE NOT NULL,       -- NIM (e.g., "22024151")
    name TEXT NOT NULL,
    class_name TEXT,
    ...
);
```

**HTML Template** (`ambil_presensi.html`):
```html
{% for student in students %}
<tr>
    <td><strong>{{ student.student_id }}</strong></td>  <!-- NIM displayed -->
    <td>{{ student.name }}</td>
    <td>
        <!-- Form uses database ID! -->
        <select name="status_{{ student.id }}">  <!-- student.id = database ID -->
            <option value="present">Hadir</option>
        </select>
    </td>
    <td>
        <input name="notes_{{ student.id }}">  <!-- Also database ID -->
    </td>
</tr>
{% endfor %}
```

### Solution: NIM-to-Database-ID Lookup

**Strategy**: Search table rows by NIM (displayed in table), then extract database ID from form field name.

**Implementation**:

```javascript
function markStudentPresent(studentId, studentName, confidence) {
    // studentId here is NIM (from face recognition)
    console.log('[Attendance] Looking for NIM:', studentId);
    
    // Search all table rows
    const rows = document.querySelectorAll('tbody tr');
    let statusSelect = null;
    let databaseId = null;
    
    for (const row of rows) {
        // Get NIM from second column (td:nth-child(2))
        const nimCell = row.querySelector('td:nth-child(2) strong');
        
        if (nimCell) {
            const nimValue = nimCell.textContent.trim();
            
            // Check if this row matches the NIM
            if (nimValue === studentId || nimValue === String(studentId)) {
                // Found it! Get the select element
                statusSelect = row.querySelector('select[name^="status_"]');
                
                if (statusSelect) {
                    // Extract database ID from name="status_123"
                    const nameAttr = statusSelect.getAttribute('name');
                    databaseId = nameAttr.replace('status_', '');
                    console.log('[Attendance] ✅ Found! NIM:', nimValue, '→ DB ID:', databaseId);
                    break;
                }
            }
        }
    }
    
    if (statusSelect && databaseId) {
        // Now we can update the form!
        statusSelect.value = 'present';
        
        // Use database ID for notes field
        const notesInput = document.querySelector(`input[name="notes_${databaseId}"]`);
        if (notesInput) {
            notesInput.value = `Face recognition - Confidence: ${(confidence * 100).toFixed(1)}%`;
        }
        
        // Highlight row
        const row = statusSelect.closest('tr');
        row.style.backgroundColor = '#d4edda';
        setTimeout(() => row.style.backgroundColor = '', 3000);
        
        // Success!
        showToast(`✅ ${studentName} berhasil diabsen!`);
    } else {
        console.error('[Attendance] ❌ NIM not found in table:', studentId);
    }
}
```

### Why This Works

1. **NIM is visible** in table (second column as `<strong>` tag)
2. **Database ID is embedded** in form field names
3. **We traverse both** to create the mapping:
   ```
   NIM (22024151) → Database ID (123)
   ```
4. **Use database ID** to update correct form fields

### Alternative Solutions (Not Used)

**Option 1**: Backend returns both IDs
```python
'student': {
    'name': name,
    'student_id': student_id,  # NIM
    'id': db_id                # Database ID
}
```
❌ Requires database query in recognition system (bad separation of concerns)

**Option 2**: Change form to use NIM
```html
<select name="status_{{ student.student_id }}">
```
❌ Requires backend changes to parse form submission differently

**Option 3**: JavaScript lookup table (current solution)
✅ No backend changes needed
✅ Works with existing database schema
✅ Clean separation of concerns

## 🎨 Video Position Fix

### Problem

**Symptom**: Video element displays **below** the card instead of inside it.

**Before**:
```
┌──────────────────────┐
│  [Camera Card]       │
│  [Placeholder]       │
└──────────────────────┘
[Video showing here]    ← WRONG! Outside card
```

**After**:
```
┌──────────────────────┐
│  [Camera Card]       │
│  [Video here]        │ ← CORRECT! Inside card
└──────────────────────┘
```

### Root Cause

Video elements with `display: block` push content down due to normal document flow, even when inside a container.

### Solution: Absolute Positioning

```html
<div class="card-body position-relative" style="height: 500px; overflow: hidden;">
    <!-- Placeholder: absolute positioned -->
    <div id="cameraPlaceholder" 
         class="position-absolute top-0 start-0 w-100 h-100" 
         style="z-index: 1;">
        <i class="bi bi-camera-video"></i>
        <p>Klik tombol di bawah untuk memulai kamera</p>
    </div>
    
    <!-- IP Camera: absolute positioned -->
    <img id="ipCameraStream" 
         class="position-absolute top-0 start-0" 
         style="display: none; width: 100%; height: 100%; object-fit: contain; z-index: 2;">
    
    <!-- Webcam: absolute positioned -->
    <video id="webcamVideoStream" 
           class="position-absolute top-0 start-0" 
           style="display: none; width: 100%; height: 100%; object-fit: contain; z-index: 2;">
    </video>
</div>
```

**Key Changes**:
1. ✅ Parent: `position-relative` with fixed `height: 500px`
2. ✅ All children: `position-absolute top-0 start-0`
3. ✅ Video/img: `width: 100%; height: 100%` to fill parent
4. ✅ `object-fit: contain` to maintain aspect ratio
5. ✅ Z-index layering: placeholder (1) → video (2)

### Benefits

- ✅ Video stays **inside** card boundaries
- ✅ No overflow to parent elements
- ✅ Smooth transitions (show/hide)
- ✅ Placeholder and video in same position

## 📊 Testing Results

### Before Fix

| Test | Result |
|------|--------|
| Face detected in backend | ✅ Pass |
| Console shows student data | ✅ Pass |
| Attendance form updates | ❌ Fail (selector not found) |
| Video position | ❌ Fail (below card) |

### After Fix

| Test | Result |
|------|--------|
| Face detected in backend | ✅ Pass |
| Console shows student data | ✅ Pass |
| NIM → Database ID lookup | ✅ Pass |
| Attendance form updates | ✅ Pass |
| Status dropdown changes | ✅ Pass |
| Notes field filled | ✅ Pass |
| Row highlighted green | ✅ Pass |
| Toast notification | ✅ Pass |
| Video position | ✅ Pass (inside card) |

## 🔍 Debugging Tips

### Check NIM vs Database ID Mismatch

**Console logs to add**:
```javascript
console.log('Received student_id:', studentId);
console.log('Found database ID:', databaseId);
console.log('Selector:', `select[name="status_${databaseId}"]`);
```

**Verify in HTML**:
```javascript
// List all student form fields
const selects = document.querySelectorAll('select[name^="status_"]');
selects.forEach(s => {
    const nimCell = s.closest('tr').querySelector('td:nth-child(2) strong');
    const nim = nimCell ? nimCell.textContent : 'N/A';
    console.log('DB ID:', s.name.replace('status_', ''), '→ NIM:', nim);
});
```

### Check Video Position

**Inspect element**:
```javascript
const video = document.getElementById('webcamVideoStream');
console.log('Position:', window.getComputedStyle(video).position);
console.log('Parent height:', video.parentElement.offsetHeight);
console.log('Video offsetTop:', video.offsetTop);
```

**Expected**:
- `position: absolute`
- `offsetTop: 0` (at top of parent)
- Parent height matches video height

## 📝 Summary

### Root Causes
1. **Database ID ≠ NIM**: Form uses database auto-increment ID, face recognition returns NIM
2. **Video overflow**: Normal document flow caused video to push outside container

### Fixes Applied
1. ✅ **NIM-to-ID lookup**: Search table by NIM, extract database ID from form field names
2. ✅ **Absolute positioning**: Stack video/placeholder with absolute positioning and z-index

### Files Modified
- `app/templates/ambil_presensi.html`:
  - Updated `markStudentPresent()` function (30+ lines)
  - Updated card-body HTML with absolute positioning
  - Added detailed console logging

### Result
- ✅ Attendance form now updates correctly when face detected
- ✅ Video stays inside card boundaries
- ✅ Green row highlight works
- ✅ Toast notifications appear
- ✅ Statistics update correctly

**Status**: FIXED ✅
