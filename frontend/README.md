# StatementSense Frontend

Modern React frontend for the StatementSense AI-powered bank statement analyzer.

## 🚀 Features

- **Modern UI/UX** - Clean, responsive design with Tailwind CSS
- **File Upload** - Drag & drop PDF upload with validation
- **Real-time Processing** - Live updates on statement processing
- **Interactive Charts** - Beautiful visualizations with Chart.js
- **Smart Categorization** - View AI-categorized transactions
- **Responsive Design** - Works perfectly on all devices
- **Error Handling** - Robust error boundaries and user feedback

## 🛠 Tech Stack

- **React 18** - Modern React with hooks
- **Vite** - Fast build tool and dev server
- **Tailwind CSS** - Utility-first CSS framework
- **React Router** - Client-side routing
- **React Query** - Server state management
- **Chart.js** - Data visualization
- **Axios** - HTTP client
- **Lucide React** - Beautiful icons

## 📦 Installation

1. **Navigate to frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Start development server:**
   ```bash
   npm run dev
   ```

4. **Open in browser:**
   Visit `http://localhost:3000`

## 🔧 Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

## 🌍 Environment Variables

Create a `.env` file in the frontend directory:

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_APP_TITLE=StatementSense
VITE_APP_DESCRIPTION=AI-Powered Bank Statement Analyzer
```

## 📁 Project Structure

```
frontend/
├── public/                 # Static assets
├── src/
│   ├── components/        # Reusable UI components
│   │   ├── Layout.jsx     # Main layout component
│   │   ├── UI.jsx         # Common UI components
│   │   └── ErrorBoundary.jsx
│   ├── pages/             # Page components
│   │   ├── Dashboard.jsx  # Main dashboard
│   │   ├── Upload.jsx     # File upload page
│   │   ├── Statements.jsx # Statements list
│   │   └── StatementDetail.jsx
│   ├── hooks/             # Custom React hooks
│   │   └── useStatements.js
│   ├── services/          # API services
│   │   └── api.js
│   ├── utils/             # Utility functions
│   │   └── helpers.js
│   ├── App.jsx           # Main app component
│   ├── main.jsx          # App entry point
│   └── index.css         # Global styles
├── package.json
├── vite.config.js
└── tailwind.config.js
```

## 🎨 UI Components

### Layout
- Responsive sidebar navigation
- Mobile-friendly hamburger menu
- Consistent header and navigation

### Pages
- **Dashboard** - Overview with quick stats and recent statements
- **Upload** - Drag & drop file upload with validation
- **Statements** - List view with filtering and sorting
- **Statement Detail** - Detailed view with charts and transaction tables

### Features
- **File Upload** - Multiple file support with progress tracking
- **Processing Status** - Real-time updates on processing status
- **Charts** - Category distribution and spending analysis
- **Filtering** - Search and filter transactions by category
- **Responsive Tables** - Mobile-optimized data tables

## 🔌 API Integration

The frontend connects to the FastAPI backend via:

- **File Upload** - `POST /api/v1/statements/upload`
- **Processing** - `POST /api/v1/statements/{id}/process`
- **Data Fetching** - `GET /api/v1/statements`
- **Transaction Details** - `GET /api/v1/statements/{id}/transactions`
- **Analysis** - `GET /api/v1/statements/{id}/analysis`

## 🎯 Key Features

### Smart File Upload
```jsx
// Drag & drop with validation
const { getRootProps, getInputProps } = useDropzone({
  accept: { 'application/pdf': ['.pdf'] },
  maxSize: 50 * 1024 * 1024, // 50MB
  onDrop: handleFileDrop
})
```

### Real-time Data
```jsx
// React Query for server state
const { data: statements, isLoading } = useStatements()
const uploadMutation = useUploadStatement()
```

### Interactive Charts
```jsx
// Chart.js integration
<Pie data={categoryData} options={chartOptions} />
<Bar data={transactionData} options={barOptions} />
```

## 🚀 Production Build

1. **Build the app:**
   ```bash
   npm run build
   ```

2. **Preview build:**
   ```bash
   npm run preview
   ```

3. **Deploy:**
   - Upload `dist/` folder to your web server
   - Configure your server to serve `index.html` for all routes
   - Set up environment variables for production

## 🔧 Customization

### Styling
- Modify `tailwind.config.js` for custom theme
- Edit `src/index.css` for global styles
- Component-specific styles use Tailwind classes

### API Configuration
- Update `src/services/api.js` for API endpoints
- Modify `vite.config.js` for proxy settings

### Adding New Pages
1. Create component in `src/pages/`
2. Add route in `src/App.jsx`
3. Update navigation in `src/components/Layout.jsx`

## 🐛 Troubleshooting

### Common Issues

**API Connection Errors:**
- Check that backend is running on `http://localhost:8000`
- Verify CORS settings in FastAPI backend
- Check environment variables

**Build Errors:**
- Clear node_modules: `rm -rf node_modules package-lock.json && npm install`
- Check for missing dependencies
- Verify Node.js version (recommended: 18+)

**Styling Issues:**
- Rebuild Tailwind: `npm run build`
- Check for conflicting CSS classes
- Verify Tailwind configuration

## 📱 Mobile Support

The app is fully responsive and optimized for:
- Mobile phones (320px+)
- Tablets (768px+)
- Desktop (1024px+)

Features include:
- Touch-friendly navigation
- Responsive tables
- Mobile-optimized forms
- Collapsible sidebar

## 🔒 Security

- No sensitive data stored in frontend
- All API calls proxied through Vite dev server
- File validation before upload
- Error boundaries prevent crashes

## 🤝 Contributing

1. Follow existing code style
2. Use TypeScript-style prop documentation
3. Add proper error handling
4. Test on multiple screen sizes
5. Update this README for new features