// Admin Offers Management JavaScript
let offersTable;
let currentEditId = null;

// Initialize on page load
$(document).ready(function() {
    initializeDataTable();
    loadStats();
    
    // Auto-refresh stats every 30 seconds
    setInterval(loadStats, 30000);
});

// Initialize DataTable
function initializeDataTable() {
    offersTable = $('#offersTable').DataTable({
        ajax: {
            url: '/api/admin/offers/list',
            dataSrc: 'data',
            error: function(xhr, error, thrown) {
                console.error('DataTables error:', error);
                showError('Failed to load offers data');
            }
        },
        columns: [
            { 
                data: 'offer_id',
                render: function(data) {
                    return `<span class="badge bg-primary">${data}</span>`;
                }
            },
            { data: 'campaign_name' },
            { 
                data: 'title',
                render: function(data, type, row) {
                    const truncated = data.length > 50 ? data.substring(0, 50) + '...' : data;
                    return `<span title="${escapeHtml(data)}">${escapeHtml(truncated)}</span>`;
                }
            },
            { 
                data: 'offer_type',
                render: function(data) {
                    const typeColors = {
                        'discount': 'success',
                        'cashback': 'info',
                        'deal': 'warning',
                        'coupon': 'primary'
                    };
                    const color = typeColors[data] || 'secondary';
                    return `<span class="badge badge-custom bg-${color}">${data}</span>`;
                }
            },
            { 
                data: 'status',
                render: function(data) {
                    const statusColors = {
                        'live': 'success',
                        'expired': 'danger',
                        'draft': 'secondary'
                    };
                    const color = statusColors[data] || 'secondary';
                    return `<span class="badge badge-custom bg-${color}">${data}</span>`;
                }
            },
            { 
                data: 'coupon_code',
                render: function(data) {
                    return data ? `<code>${data}</code>` : '<span class="text-muted">-</span>';
                }
            },
            { 
                data: 'start_date',
                render: function(data) {
                    return data ? formatDate(data) : '<span class="text-muted">-</span>';
                }
            },
            { 
                data: 'end_date',
                render: function(data) {
                    return data ? formatDate(data) : '<span class="text-muted">-</span>';
                }
            },
            {
                data: null,
                orderable: false,
                render: function(data, type, row) {
                    return `
                        <button class="btn btn-sm btn-info action-btn" onclick="viewOffer(${row.id})" title="View">
                            <i class="fas fa-eye"></i>
                        </button>
                        <button class="btn btn-sm btn-warning action-btn" onclick="editOffer(${row.id})" title="Edit">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn btn-sm btn-danger action-btn" onclick="deleteOffer(${row.id}, '${escapeHtml(row.title)}')" title="Delete">
                            <i class="fas fa-trash"></i>
                        </button>
                    `;
                }
            }
        ],
        responsive: true,
        pageLength: 25,
        order: [[0, 'desc']],
        language: {
            search: "_INPUT_",
            searchPlaceholder: "Search offers...",
            lengthMenu: "Show _MENU_ offers"
        },
        drawCallback: function() {
            // Apply custom styling after draw
            $('.dataTables_paginate .pagination').addClass('pagination-sm');
        }
    });
}

// Load statistics
async function loadStats() {
    try {
        const response = await fetch('/api/admin/offers/stats/summary');
        const result = await response.json();
        
        if (result.success) {
            $('#totalOffersCount').text(result.data.total_offers);
            $('#liveOffersCount').text(result.data.live_offers);
            $('#totalCampaignsCount').text(result.data.total_campaigns);
            $('#totalEmbeddingsCount').text(result.data.total_embeddings);
        }
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

// Show create modal
function showCreateModal() {
    currentEditId = null;
    $('#offerModalTitle').html('<i class="fas fa-plus-circle me-2"></i>Create New Offer');
    $('#offerForm')[0].reset();
    $('#offerId').val('');
    
    // Set default values
    $('#offerType').val('discount');
    $('#status').val('live');
    $('#categories').val('{"11": "General"}');
    
    new bootstrap.Modal(document.getElementById('offerModal')).show();
}

// View offer details
async function viewOffer(id) {
    showSpinner();
    
    try {
        const response = await fetch(`/api/admin/offers/${id}`);
        const result = await response.json();
        
        if (result.success) {
            const offer = result.data;
            
            let categoriesHtml = '';
            if (offer.categories) {
                const cats = Object.values(offer.categories);
                categoriesHtml = cats.map(cat => `<span class="badge bg-info me-1">${cat}</span>`).join('');
            }
            
            const content = `
                <div class="row">
                    <div class="col-md-6">
                        <p><strong>Offer ID:</strong> <span class="badge bg-primary">${offer.offer_id}</span></p>
                        <p><strong>Campaign:</strong> ${escapeHtml(offer.campaign_name)}</p>
                        <p><strong>Title:</strong> ${escapeHtml(offer.title)}</p>
                        <p><strong>Type:</strong> <span class="badge bg-success">${offer.offer_type}</span></p>
                        <p><strong>Status:</strong> <span class="badge bg-${offer.status === 'live' ? 'success' : 'danger'}">${offer.status}</span></p>
                    </div>
                    <div class="col-md-6">
                        <p><strong>Coupon Code:</strong> ${offer.coupon_code ? `<code>${offer.coupon_code}</code>` : '-'}</p>
                        <p><strong>Start Date:</strong> ${offer.start_date ? formatDate(offer.start_date) : '-'}</p>
                        <p><strong>End Date:</strong> ${offer.end_date ? formatDate(offer.end_date) : '-'}</p>
                        <p><strong>Categories:</strong> ${categoriesHtml || '-'}</p>
                    </div>
                </div>
                <hr>
                <div class="mb-3">
                    <strong>Description:</strong>
                    <div class="border rounded p-2 mt-2">${offer.description || '-'}</div>
                </div>
                ${offer.terms_and_conditions ? `
                <div class="mb-3">
                    <strong>Terms & Conditions:</strong>
                    <div class="border rounded p-2 mt-2">${offer.terms_and_conditions}</div>
                </div>
                ` : ''}
                <div class="mb-3">
                    <strong>URL:</strong> <a href="${offer.url}" target="_blank">${offer.url}</a>
                </div>
                <div class="mb-3">
                    <strong>Affiliate URL:</strong> <a href="${offer.affiliate_url}" target="_blank">${offer.affiliate_url}</a>
                </div>
                ${offer.image_url ? `
                <div class="mb-3">
                    <strong>Image:</strong><br>
                    <img src="${offer.image_url}" alt="Offer Image" style="max-width: 200px;" class="img-thumbnail">
                </div>
                ` : ''}
            `;
            
            $('#viewOfferContent').html(content);
            new bootstrap.Modal(document.getElementById('viewOfferModal')).show();
        } else {
            showError('Failed to load offer details');
        }
    } catch (error) {
        console.error('Error viewing offer:', error);
        showError('Failed to load offer details');
    } finally {
        hideSpinner();
    }
}

// Edit offer
async function editOffer(id) {
    showSpinner();
    
    try {
        const response = await fetch(`/api/admin/offers/${id}`);
        const result = await response.json();
        
        if (result.success) {
            const offer = result.data;
            currentEditId = id;
            
            $('#offerModalTitle').html('<i class="fas fa-edit me-2"></i>Edit Offer');
            $('#offerId').val(id);
            $('#campaignId').val(offer.campaign_id || '');
            $('#campaignName').val(offer.campaign_name || '');
            $('#title').val(offer.title || '');
            $('#description').val(offer.description || '');
            $('#url').val(offer.url || '');
            $('#affiliateUrl').val(offer.affiliate_url || '');
            $('#offerType').val(offer.offer_type || 'discount');
            $('#status').val(offer.status || 'live');
            $('#couponCode').val(offer.coupon_code || '');
            $('#imageUrl').val(offer.image_url || '');
            $('#termsConditions').val(offer.terms_and_conditions || '');
            
            // Format dates for input fields
            if (offer.start_date) {
                $('#startDate').val(offer.start_date.split('T')[0]);
            }
            if (offer.end_date) {
                $('#endDate').val(offer.end_date.split('T')[0]);
            }
            
            // Format categories as JSON
            if (offer.categories) {
                $('#categories').val(JSON.stringify(offer.categories, null, 2));
            }
            
            new bootstrap.Modal(document.getElementById('offerModal')).show();
        } else {
            showError('Failed to load offer for editing');
        }
    } catch (error) {
        console.error('Error loading offer:', error);
        showError('Failed to load offer for editing');
    } finally {
        hideSpinner();
    }
}

// Save offer (create or update)
async function saveOffer() {
    // Validate form
    const form = document.getElementById('offerForm');
    if (!form.checkValidity()) {
        form.reportValidity();
        return;
    }
    
    showSpinner();
    
    try {
        // Parse categories JSON
        let categories = {};
        try {
            const categoriesText = $('#categories').val().trim();
            if (categoriesText) {
                categories = JSON.parse(categoriesText);
            }
        } catch (e) {
            hideSpinner();
            showError('Invalid JSON format for categories');
            return;
        }
        
        // Build request data
        const offerData = {
            campaign_id: parseInt($('#campaignId').val()),
            campaign: $('#campaignName').val(),
            title: $('#title').val(),
            description: $('#description').val(),
            terms_and_condition: $('#termsConditions').val(),
            coupon_code: $('#couponCode').val(),
            image_url: $('#imageUrl').val(),
            type: $('#offerType').val(),
            status: $('#status').val(),
            url: $('#url').val(),
            affiliate_url: $('#affiliateUrl').val(),
            start_date: $('#startDate').val(),
            end_date: $('#endDate').val(),
            categories: categories
        };
        
        let url, method;
        if (currentEditId) {
            // Update existing offer
            url = `/api/admin/offers/${currentEditId}`;
            method = 'PUT';
        } else {
            // Create new offer
            url = '/api/admin/offers/create';
            method = 'POST';
        }
        
        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(offerData)
        });
        
        const result = await response.json();
        
        if (result.success) {
            showSuccess(currentEditId ? 'Offer updated successfully!' : 'Offer created successfully!');
            bootstrap.Modal.getInstance(document.getElementById('offerModal')).hide();
            refreshTable();
        } else {
            showError(result.message || 'Failed to save offer');
        }
    } catch (error) {
        console.error('Error saving offer:', error);
        showError('Failed to save offer: ' + error.message);
    } finally {
        hideSpinner();
    }
}

// Delete offer
async function deleteOffer(id, title) {
    const result = await Swal.fire({
        title: 'Are you sure?',
        html: `Do you want to delete the offer: <br><strong>${escapeHtml(title)}</strong>?`,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#ef4444',
        cancelButtonColor: '#6c757d',
        confirmButtonText: 'Yes, delete it!',
        cancelButtonText: 'Cancel'
    });
    
    if (result.isConfirmed) {
        showSpinner();
        
        try {
            const response = await fetch(`/api/admin/offers/${id}`, {
                method: 'DELETE'
            });
            
            const result = await response.json();
            
            if (result.success) {
                showSuccess('Offer deleted successfully!');
                refreshTable();
            } else {
                showError(result.message || 'Failed to delete offer');
            }
        } catch (error) {
            console.error('Error deleting offer:', error);
            showError('Failed to delete offer');
        } finally {
            hideSpinner();
        }
    }
}

// Sync offers with API
async function syncOffers() {
    const result = await Swal.fire({
        title: 'Sync with Cuelinks API?',
        text: 'This will fetch all offers from Cuelinks API and extended offers. This may take a few minutes.',
        icon: 'question',
        showCancelButton: true,
        confirmButtonColor: '#10b981',
        cancelButtonColor: '#6c757d',
        confirmButtonText: 'Yes, start sync!',
        cancelButtonText: 'Cancel'
    });
    
    if (result.isConfirmed) {
        showSpinner();
        
        try {
            const response = await fetch('/api/offers-sync/sync-now?clear_data=true', {
                method: 'POST'
            });
            
            const result = await response.json();
            
            if (result.success) {
                const message = result.message || `Successfully synced ${result.total_offers_retrieved || 0} offers`;
                showSuccess(message);
                refreshTable();
            } else {
                showError(result.error || 'Sync failed');
            }
        } catch (error) {
            console.error('Error syncing offers:', error);
            showError('Failed to sync offers');
        } finally {
            hideSpinner();
        }
    }
}

// Refresh table
function refreshTable() {
    offersTable.ajax.reload(null, false);
    loadStats();
}

// Utility functions
function showSpinner() {
    $('#loadingSpinner').css('display', 'flex');
}

function hideSpinner() {
    $('#loadingSpinner').css('display', 'none');
}

function showSuccess(message) {
    Swal.fire({
        icon: 'success',
        title: 'Success!',
        text: message,
        timer: 3000,
        showConfirmButton: false
    });
}

function showError(message) {
    Swal.fire({
        icon: 'error',
        title: 'Error!',
        text: message,
        confirmButtonColor: '#6366f1'
    });
}

function formatDate(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
}

function escapeHtml(text) {
    if (!text) return '';
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.toString().replace(/[&<>"']/g, m => map[m]);
}
