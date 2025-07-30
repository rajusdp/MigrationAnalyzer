/**
 * TypeScript type definitions for the Migration Estimator application
 */

// User and Authentication Types
export type UserRole = 'end_user' | 'sales' | 'admin';

export interface User {
  id: number;
  email: string;
  role: UserRole;
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface AuthToken {
  accessToken: string;
  tokenType: string;
  expiresIn: number;
  user: User;
}

// Form Data Types
export interface StakeholderContact {
  email: string;
  title: string;
  phone: string;
}

export type CollaborationScope = 'Internal only' | 'External via Slack Connect' | 'Both';
export type O365License = 'E1' | 'E3' | 'E5' | 'F1' | 'F3' | 'Business Basic' | 'Business Standard' | 'Business Premium' | 'None';

export interface CustomerInfo {
  companyName: string;
  contactName: string;
  email: string;
  phone: string;
  projectLead: string;
  itContact: string;
  roughBudget: number;
  idealTimeline: string; // ISO date string
  otherStakeholders: 'yes' | 'no';
  stakeholderContacts?: StakeholderContact[];
  slackRenewal: string;
  slackCancellation: string;
  totalLicenses: number;
  collaborationScope: CollaborationScope;
  supportExternalUsecases?: 'Support in Teams' | 'Continue Slack';
  otherCollabTools: string[];
}

export interface TechnicalDetails {
  adIntegration: 'yes' | 'no';
  o365UserAssumption?: 'yes' | 'no';
  analyticsReportFilename: string;
  messageVolume: number;
  migrationCriteria: string;
  installedApps: string;
  customApps: string[];
  customAppDetails?: string;
  thirdPartyApps: string[];
  thirdPartyAppDetails?: string;
  integrations: string;
  governancePolicy: string;
  contentRestrictions: string;
  enterpriseSearch: string;
  usagePattern: string;
  o365CurrentUsage: O365License;
  slackCanvasUsage?: string;
  slackListsUsage?: string;
}

export interface FormData {
  customerInfo: Partial<CustomerInfo>;
  technicalDetails: Partial<TechnicalDetails>;
}

// Estimate Types
export interface EstimateBreakdown {
  baseCost: number;
  additionalTiers: number;
  addonServiceCost: number;
  dataPrepCost: number;
  totalCost: number;
  messageVolume: number;
}

export interface EstimateTimeline {
  baseWeeks: number;
  additionalWeeks: number;
  totalWeeks: number;
}

export interface Estimate {
  cost: number;
  effortWeeks: number;
  timelineWeeks: number;
  breakdown: EstimateBreakdown;
  timeline: EstimateTimeline;
  createdAt: string;
}

// Submission Types
export type SubmissionStatus = 'New' | 'Contacted' | 'In Negotiation' | 'Closed Won' | 'Closed Lost';

export interface Submission {
  id: number;
  userId: number;
  status: SubmissionStatus;
  salesComments?: string;
  cost?: number;
  effortWeeks?: number;
  createdAt: string;
  updatedAt: string;
  estimate?: Estimate;
}

export interface SubmissionRequest {
  customerInfo: CustomerInfo;
  technicalDetails: TechnicalDetails;
}

export interface SubmissionUpdate {
  status?: SubmissionStatus;
  salesComments?: string;
}

// API Response Types
export interface BaseResponse {
  success: boolean;
  message?: string;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  pageSize: number;
  hasNext: boolean;
  hasPrev: boolean;
}

export interface PDFResponse {
  downloadUrl: string;
  expiresAt: string;
  fileSize?: number;
}

// UI State Types
export interface FormValidationState {
  isValid: boolean;
  errors: Record<string, string>;
  touchedFields: Set<string>;
}

export interface FormStep {
  id: string;
  title: string;
  description: string;
  isCompleted: boolean;
  isActive: boolean;
  completionPercentage: number;
}

export interface NotificationState {
  type: 'success' | 'error' | 'warning' | 'info';
  message: string;
  id: string;
  duration?: number;
}

// Redux Store Types
export interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

export interface FormState {
  currentStep: number;
  formData: FormData;
  validation: FormValidationState;
  autoSaveStatus: 'idle' | 'saving' | 'saved' | 'error';
  lastSaved: string | null;
}

export interface SubmissionsState {
  submissions: Submission[];
  currentSubmission: Submission | null;
  isLoading: boolean;
  error: string | null;
  filters: {
    status?: SubmissionStatus;
    dateRange?: [string, string];
  };
}

export interface EstimatesState {
  currentEstimate: Estimate | null;
  isCalculating: boolean;
  error: string | null;
  addonServices: Record<string, number>;
}

export interface UIState {
  notifications: NotificationState[];
  sidebarOpen: boolean;
  theme: 'light' | 'dark';
  loading: {
    global: boolean;
    components: Record<string, boolean>;
  };
}

export interface RootState {
  auth: AuthState;
  form: FormState;
  submissions: SubmissionsState;
  estimates: EstimatesState;
  ui: UIState;
}

// Chart Data Types
export interface ChartDataPoint {
  name: string;
  value: number;
  color?: string;
  label?: string;
}

export interface TimelineData {
  phase: string;
  startWeek: number;
  endWeek: number;
  description: string;
  color: string;
}

// File Upload Types
export interface FileUpload {
  file: File;
  uploadProgress: number;
  uploadStatus: 'pending' | 'uploading' | 'completed' | 'error';
  uploadError?: string;
  downloadUrl?: string;
}

// Dashboard Types
export interface DashboardStats {
  totalSubmissions: number;
  avgCost: number;
  avgTimeline: number;
  statusBreakdown: Record<SubmissionStatus, number>;
  recentActivity: DashboardActivity[];
}

export interface DashboardActivity {
  id: string;
  type: 'submission_created' | 'status_updated' | 'pdf_generated';
  title: string;
  description: string;
  timestamp: string;
  userId: number;
  submissionId?: number;
}

// Error Types
export interface APIError {
  message: string;
  code?: string;
  details?: Record<string, any>;
  timestamp: string;
}

export interface ValidationError {
  field: string;
  message: string;
  code: string;
}

// Audit Types
export interface AuditLog {
  id: number;
  actorId: number;
  timestamp: string;
  entity: string;
  action: string;
  entityId: number;
  diff: Record<string, any>;
  ipAddress?: string;
  userAgent?: string;
}

// Feature Flag Types
export interface FeatureFlags {
  pdfGeneration: boolean;
  emailNotifications: boolean;
  advancedAnalytics: boolean;
  experimentalFeatures: boolean;
}

// Component Props Types
export interface BaseComponentProps {
  className?: string;
  children?: React.ReactNode;
}

export interface FormFieldProps extends BaseComponentProps {
  name: string;
  label: string;
  required?: boolean;
  disabled?: boolean;
  error?: string;
}

export interface ModalProps extends BaseComponentProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  size?: 'sm' | 'md' | 'lg' | 'xl';
}

export interface TableColumn<T> {
  key: keyof T;
  title: string;
  sortable?: boolean;
  render?: (value: any, row: T) => React.ReactNode;
  width?: string;
}

export interface TableProps<T> extends BaseComponentProps {
  data: T[];
  columns: TableColumn<T>[];
  loading?: boolean;
  emptyMessage?: string;
  onRowClick?: (row: T) => void;
}
