document.addEventListener('DOMContentLoaded', () => {
    const dropZone = DOM.el('#drop-zone');
    const fileInput = DOM.el('#file-input');
    
    if(!dropZone) return;

    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, preventDefaults, false);
    });
    
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => {
            dropZone.classList.remove('bg-surface-container-lowest');
            dropZone.classList.add('bg-surface-container-low');
        }, false);
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => {
            dropZone.classList.remove('bg-surface-container-low');
            dropZone.classList.add('bg-surface-container-lowest');
        }, false);
    });
    
    dropZone.addEventListener('drop', (e) => {
        const files = e.dataTransfer.files;
        handleFiles(files);
    });
    
    fileInput.addEventListener('change', (e) => {
        handleFiles(e.target.files);
    });
});

function handleFiles(files) {
    const fileList = DOM.el('#upload-list');
    DOM.el('#upload-status').style.display = 'block';
    
    [...files].forEach(file => {
        // Validate file type
        const validTypes = ['application/pdf', 'image/png', 'image/jpeg'];
        if (!validTypes.includes(file.type)) {
            alert(`File type not supported: ${file.name}`);
            return;
        }
        
        const fileId = 'file-' + Date.now() + '-' + Math.floor(Math.random() * 1000);
        const size = (file.size / (1024 * 1024)).toFixed(2) + ' MB';
        
        const fileEl = document.createElement('div');
        fileEl.className = "flex flex-col gap-2 p-4 border border-outline-variant rounded bg-surface-container-lowest";
        fileEl.innerHTML = `
            <div class="flex justify-between items-center">
                <div class="flex items-center gap-3">
                    <span class="material-symbols-outlined text-on-surface-variant text-xl">description</span>
                    <div>
                        <div class="text-[11px] font-black">${file.name}</div>
                        <div class="text-[9px] text-on-surface-variant font-medium">${size}</div>
                    </div>
                </div>
                <div class="text-[10px] font-black uppercase text-on-surface-variant" id="status-${fileId}">Uploading...</div>
            </div>
            <div class="w-full bg-surface-container h-1.5 rounded overflow-hidden">
                <div class="bg-primary h-full transition-all duration-300" style="width: 0%" id="progress-${fileId}"></div>
            </div>
        `;
        
        fileList.prepend(fileEl);
        simulateUpload(fileId, file);
    });
}

async function simulateUpload(fileId, file) {
    const progressBar = DOM.el(`#progress-${fileId}`);
    const statusText = DOM.el(`#status-${fileId}`);
    
    // Global Elements
    const globalProgress = DOM.el('#global-progress-bar');
    const globalStatus = DOM.el('#global-status-text');
    
    progressBar.style.width = '10%';
    if(globalProgress) {
        globalProgress.style.width = '10%';
        globalProgress.className = 'bg-primary h-full transition-all duration-300';
    }
    if(globalStatus) {
        globalStatus.textContent = 'Uploading to API Gateway...';
        globalStatus.className = 'text-primary font-bold';
    }
    
    try {
        // Read file as base64
        const base64Data = await new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = () => resolve(reader.result.split(',')[1]); // Extract base64 part
            reader.onerror = error => reject(error);
            reader.readAsDataURL(file);
        });
        
        const payload = {
            userId: 'user143',
            fileName: file.name,
            fileType: file.type || 'application/octet-stream',
            billType: 'Utility',
            fileData: base64Data
        };
        
        // Using the live API gateway with the required JSON schema
        const response = await API.post('upload', payload);
        
        if (response.success) {
            progressBar.style.width = '100%';
            statusText.textContent = 'Processed Successfully';
            statusText.className = 'text-[10px] font-black uppercase text-primary';
            
            if(globalProgress) globalProgress.style.width = '100%';
            if(globalStatus) globalStatus.textContent = 'Processing Complete. Logs Generated.';
        } else {
            throw new Error(response.message || 'Upload failed');
        }
    } catch (error) {
        progressBar.style.width = '100%';
        progressBar.className = 'bg-error h-full transition-all duration-300';
        statusText.textContent = 'API Error - Check Logs';
        statusText.className = 'text-[10px] font-black uppercase text-error';
        
        if(globalProgress) {
            globalProgress.style.width = '100%';
            globalProgress.className = 'bg-error h-full transition-all duration-300';
        }
        if(globalStatus) {
            globalStatus.textContent = 'API Gateway Error (Endpoint Missing)';
            globalStatus.className = 'text-error font-bold';
        }
        console.error("Upload error:", error);
    }
}
