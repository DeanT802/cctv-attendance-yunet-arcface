/*
Video Element Diagnostic Tool
============================
Paste this script into browser console (F12) to diagnose video visibility issues.

Usage:
1. Open browser console (F12)
2. Copy-paste entire script
3. Press Enter
4. Read diagnostic output
*/

console.log('='.repeat(80));
console.log('VIDEO ELEMENT DIAGNOSTIC TOOL');
console.log('='.repeat(80));

// Get elements
const ipCamera = document.getElementById('ipCameraStream');
const webcamVideo = document.getElementById('webcamVideoStream');
const placeholder = document.getElementById('cameraPlaceholder');
const container = document.querySelector('.card-body.position-relative');

console.log('\n📋 ELEMENT EXISTENCE CHECK');
console.log('-'.repeat(80));
console.log('IP Camera element:', ipCamera ? '✅ EXISTS' : '❌ NOT FOUND');
console.log('Webcam video element:', webcamVideo ? '✅ EXISTS' : '❌ NOT FOUND');
console.log('Placeholder element:', placeholder ? '✅ EXISTS' : '❌ NOT FOUND');
console.log('Container element:', container ? '✅ EXISTS' : '❌ NOT FOUND');

if (!ipCamera || !webcamVideo || !placeholder) {
    console.error('❌ CRITICAL: Some elements not found! Check HTML structure.');
}

// IP Camera diagnostics
if (ipCamera) {
    console.log('\n📹 IP CAMERA DIAGNOSTICS');
    console.log('-'.repeat(80));
    
    const ipComputedStyle = window.getComputedStyle(ipCamera);
    const ipRect = ipCamera.getBoundingClientRect();
    
    console.log('Inline Styles:');
    console.log('  display:', ipCamera.style.display || 'not set');
    console.log('  visibility:', ipCamera.style.visibility || 'not set');
    console.log('  opacity:', ipCamera.style.opacity || 'not set');
    console.log('  z-index:', ipCamera.style.zIndex || 'not set');
    
    console.log('\nComputed Styles (Final):');
    console.log('  display:', ipComputedStyle.display, ipComputedStyle.display === 'block' ? '✅' : '❌');
    console.log('  visibility:', ipComputedStyle.visibility, ipComputedStyle.visibility === 'visible' ? '✅' : '❌');
    console.log('  opacity:', ipComputedStyle.opacity, ipComputedStyle.opacity === '1' ? '✅' : '❌');
    console.log('  z-index:', ipComputedStyle.zIndex);
    console.log('  position:', ipComputedStyle.position);
    
    console.log('\nDimensions & Position:');
    console.log('  width:', ipRect.width + 'px', ipRect.width > 0 ? '✅' : '❌ (COLLAPSED!)');
    console.log('  height:', ipRect.height + 'px', ipRect.height > 0 ? '✅' : '❌ (COLLAPSED!)');
    console.log('  top:', ipRect.top + 'px');
    console.log('  left:', ipRect.left + 'px');
    console.log('  right:', ipRect.right + 'px');
    console.log('  bottom:', ipRect.bottom + 'px');
    
    console.log('\nImage Source:');
    console.log('  src:', ipCamera.src || '(empty)');
    console.log('  complete:', ipCamera.complete);
    console.log('  naturalWidth:', ipCamera.naturalWidth);
    console.log('  naturalHeight:', ipCamera.naturalHeight);
    
    console.log('\nClasses:');
    console.log('  classList:', ipCamera.className || '(no classes)');
    const hasHidingClass = ipCamera.classList.contains('d-none') || 
                           ipCamera.classList.contains('invisible') ||
                           ipCamera.classList.contains('opacity-0');
    if (hasHidingClass) {
        console.warn('  ⚠️ WARNING: Element has hiding Bootstrap class!');
    }
}

// Webcam diagnostics
if (webcamVideo) {
    console.log('\n🎥 WEBCAM VIDEO DIAGNOSTICS');
    console.log('-'.repeat(80));
    
    const webcamComputedStyle = window.getComputedStyle(webcamVideo);
    const webcamRect = webcamVideo.getBoundingClientRect();
    
    console.log('Inline Styles:');
    console.log('  display:', webcamVideo.style.display || 'not set');
    console.log('  visibility:', webcamVideo.style.visibility || 'not set');
    console.log('  opacity:', webcamVideo.style.opacity || 'not set');
    console.log('  z-index:', webcamVideo.style.zIndex || 'not set');
    
    console.log('\nComputed Styles (Final):');
    console.log('  display:', webcamComputedStyle.display, webcamComputedStyle.display === 'block' ? '✅' : '❌');
    console.log('  visibility:', webcamComputedStyle.visibility, webcamComputedStyle.visibility === 'visible' ? '✅' : '❌');
    console.log('  opacity:', webcamComputedStyle.opacity, webcamComputedStyle.opacity === '1' ? '✅' : '❌');
    console.log('  z-index:', webcamComputedStyle.zIndex);
    console.log('  position:', webcamComputedStyle.position);
    
    console.log('\nDimensions & Position:');
    console.log('  width:', webcamRect.width + 'px', webcamRect.width > 0 ? '✅' : '❌ (COLLAPSED!)');
    console.log('  height:', webcamRect.height + 'px', webcamRect.height > 0 ? '✅' : '❌ (COLLAPSED!)');
    console.log('  top:', webcamRect.top + 'px');
    console.log('  left:', webcamRect.left + 'px');
    
    console.log('\nVideo Stream:');
    console.log('  srcObject:', webcamVideo.srcObject ? '✅ SET' : '❌ NOT SET');
    console.log('  videoWidth:', webcamVideo.videoWidth);
    console.log('  videoHeight:', webcamVideo.videoHeight);
    console.log('  readyState:', webcamVideo.readyState, 
                 webcamVideo.readyState >= 2 ? '✅ (HAVE_CURRENT_DATA or better)' : '❌');
    console.log('  paused:', webcamVideo.paused, webcamVideo.paused ? '❌ (VIDEO PAUSED!)' : '✅');
}

// Placeholder diagnostics
if (placeholder) {
    console.log('\n📍 PLACEHOLDER DIAGNOSTICS');
    console.log('-'.repeat(80));
    
    const placeholderComputedStyle = window.getComputedStyle(placeholder);
    const placeholderRect = placeholder.getBoundingClientRect();
    
    console.log('Computed Styles:');
    console.log('  display:', placeholderComputedStyle.display);
    console.log('  visibility:', placeholderComputedStyle.visibility);
    console.log('  opacity:', placeholderComputedStyle.opacity);
    console.log('  z-index:', placeholderComputedStyle.zIndex);
    
    console.log('\nDimensions:');
    console.log('  width:', placeholderRect.width + 'px');
    console.log('  height:', placeholderRect.height + 'px');
    
    const isBlocking = placeholderComputedStyle.display !== 'none' && 
                       placeholderRect.width > 0 && 
                       placeholderRect.height > 0;
    
    if (isBlocking) {
        console.warn('  ⚠️ WARNING: Placeholder is visible and may be blocking video!');
    } else {
        console.log('  ✅ Placeholder properly hidden');
    }
}

// Container diagnostics
if (container) {
    console.log('\n📦 CONTAINER DIAGNOSTICS');
    console.log('-'.repeat(80));
    
    const containerComputedStyle = window.getComputedStyle(container);
    const containerRect = container.getBoundingClientRect();
    
    console.log('Position:');
    console.log('  position:', containerComputedStyle.position, 
                 containerComputedStyle.position === 'relative' ? '✅' : '❌ (Should be relative!)');
    console.log('  overflow:', containerComputedStyle.overflow);
    
    console.log('\nDimensions:');
    console.log('  width:', containerRect.width + 'px', containerRect.width > 0 ? '✅' : '❌');
    console.log('  height:', containerRect.height + 'px', containerRect.height > 0 ? '✅' : '❌');
}

// Z-index comparison
console.log('\n🔢 Z-INDEX STACKING ORDER');
console.log('-'.repeat(80));
const ipZIndex = ipCamera ? parseInt(window.getComputedStyle(ipCamera).zIndex) || 0 : 0;
const webcamZIndex = webcamVideo ? parseInt(window.getComputedStyle(webcamVideo).zIndex) || 0 : 0;
const placeholderZIndex = placeholder ? parseInt(window.getComputedStyle(placeholder).zIndex) || 0 : 0;

console.log('Placeholder z-index:', placeholderZIndex);
console.log('IP Camera z-index:', ipZIndex);
console.log('Webcam Video z-index:', webcamZIndex);

if (ipZIndex > placeholderZIndex && webcamZIndex > placeholderZIndex) {
    console.log('✅ Z-index stacking correct (video > placeholder)');
} else {
    console.error('❌ Z-index issue! Video should have higher z-index than placeholder!');
}

// Backend stream check
console.log('\n🌐 BACKEND STREAM CHECK');
console.log('-'.repeat(80));
console.log('Testing IP Camera stream endpoint...');

fetch('/presensi_face/ip_stream')
    .then(response => {
        if (response.ok) {
            console.log('✅ Backend stream endpoint accessible');
            console.log('   Status:', response.status);
            console.log('   Content-Type:', response.headers.get('Content-Type'));
        } else {
            console.error('❌ Backend stream endpoint error:', response.status, response.statusText);
        }
    })
    .catch(error => {
        console.error('❌ Failed to reach backend stream endpoint:', error.message);
    });

// Summary and recommendations
console.log('\n📊 DIAGNOSTIC SUMMARY');
console.log('-'.repeat(80));

const issues = [];
const warnings = [];

if (ipCamera) {
    const ipStyle = window.getComputedStyle(ipCamera);
    const ipRect = ipCamera.getBoundingClientRect();
    
    if (ipStyle.display === 'none') {
        issues.push('IP Camera display is "none" - should be "block" when active');
    }
    if (ipStyle.visibility === 'hidden') {
        issues.push('IP Camera visibility is "hidden" - should be "visible" when active');
    }
    if (ipStyle.opacity === '0') {
        issues.push('IP Camera opacity is 0 - should be 1 when active');
    }
    if (ipRect.width === 0 || ipRect.height === 0) {
        issues.push('IP Camera has zero dimensions - element is collapsed!');
    }
    if (!ipCamera.src || ipCamera.src === window.location.href) {
        warnings.push('IP Camera src not set or pointing to current page');
    }
}

if (placeholder) {
    const placeholderStyle = window.getComputedStyle(placeholder);
    const placeholderRect = placeholder.getBoundingClientRect();
    
    if (placeholderStyle.display !== 'none' && ipCamera && window.getComputedStyle(ipCamera).display === 'block') {
        warnings.push('Both placeholder and video visible at same time');
    }
}

if (issues.length > 0) {
    console.log('\n❌ ISSUES FOUND:');
    issues.forEach((issue, i) => console.log(`  ${i + 1}. ${issue}`));
} else {
    console.log('\n✅ No critical issues found!');
}

if (warnings.length > 0) {
    console.log('\n⚠️ WARNINGS:');
    warnings.forEach((warning, i) => console.log(`  ${i + 1}. ${warning}`));
}

console.log('\n💡 RECOMMENDATIONS:');
console.log('-'.repeat(80));
console.log('1. If video not showing:');
console.log('   - Hard refresh browser: Ctrl + F5 (Chrome) or Ctrl + Shift + R (Firefox)');
console.log('   - Clear browser cache completely');
console.log('   - Check console for JavaScript errors');
console.log('');
console.log('2. If dimensions are 0:');
console.log('   - Check parent container has non-zero height');
console.log('   - Verify CSS position: absolute on video element');
console.log('   - Check for CSS conflicts in external stylesheets');
console.log('');
console.log('3. If z-index not working:');
console.log('   - Ensure parent has position: relative (or absolute/fixed)');
console.log('   - Check for transform/filter/perspective on parent (creates stacking context)');
console.log('   - Use higher z-index value (e.g., 9999)');
console.log('');
console.log('4. If stream not loading:');
console.log('   - Test endpoint directly: http://YOUR_IP:5000/presensi_face/ip_stream');
console.log('   - Check backend logs for RTSP errors');
console.log('   - Verify RTSP camera URL in .env file');

console.log('\n' + '='.repeat(80));
console.log('DIAGNOSTIC COMPLETE');
console.log('='.repeat(80));
