document.addEventListener('DOMContentLoaded', () => {
    // Get references to DOM elements
    const dropArea = document.getElementById('drop-area');
    const fileInput = document.getElementById('file');
    const uploadForm = document.getElementById('upload-form');
    
    // Add event listeners for drag and drop functionality
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, preventDefaults, false);
    });
    
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    // Highlight drop area when drag enters
    ['dragenter', 'dragover'].forEach(eventName => {
        dropArea.addEventListener(eventName, highlight, false);
    });
    
    // Remove highlight when drag leaves
    ['dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, unhighlight, false);
    });
    
    function highlight() {
        dropArea.classList.add('highlight');
    }
    
    function unhighlight() {
        dropArea.classList.remove('highlight');
    }
    
    // Handle dropped files
    dropArea.addEventListener('drop', handleDrop, false);
    
    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        
        if (files.length) {
            fileInput.files = files;
            // Add visual feedback that file was selected
            const fileName = files[0].name;
            updateFileStatus(fileName);
            
            // Submit the form automatically if a file is dropped
            uploadForm.submit();
        }
    }
    
    // Handle regular file input change
    fileInput.addEventListener('change', (e) => {
        if (fileInput.files.length) {
            const fileName = fileInput.files[0].name;
            updateFileStatus(fileName);
        }
    });
    
    function updateFileStatus(fileName) {
        // Create or update file status message
        let statusElement = document.querySelector('.file-status');
        
        if (!statusElement) {
            statusElement = document.createElement('p');
            statusElement.className = 'file-status';
            dropArea.querySelector('.file-input-wrapper').appendChild(statusElement);
        }
        
        statusElement.textContent = Selected file: ${fileName};
        statusElement.style.color = 'var(--success-color)';
        statusElement.style.marginTop = '1rem';
    }
    
    // Ripple effect for buttons
    const buttons = document.querySelectorAll('.ripple');
    
    buttons.forEach(button => {
        button.addEventListener('click', function(e) {
            // Remove any existing ripple elements
            const ripples = button.getElementsByClassName('ripple-effect');
            while (ripples.length > 0) {
                ripples[0].remove();
            }
            
            const ripple = document.createElement('span');
            ripple.classList.add('ripple-effect');
            
            const rect = button.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);
            
            ripple.style.width = ripple.style.height = ${size}px;
            ripple.style.left = ${e.clientX - rect.left - size / 2}px;
            ripple.style.top = ${e.clientY - rect.top - size / 2}px;
            
            button.appendChild(ripple);
            
            // Remove the ripple element after animation completes
            setTimeout(() => {
                if (ripple) {
                    ripple.remove();
                }
            }, 600);
        });
    });
    
    // Active nav link highlighting
    const currentLocation = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-link');
    
    navLinks.forEach(link => {
        const linkPath = link.getAttribute('href');
        if ((currentLocation === '/' && linkPath === '/') || 
            (currentLocation !== '/' && linkPath !== '/' && currentLocation.includes(linkPath))) {
            link.classList.add('active');
        } else {
            link.classList.remove('active');
        }
    });
});