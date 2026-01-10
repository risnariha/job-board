import React, { useState, useEffect } from 'react';
import { Form, Row, Col, Spinner, Alert } from 'react-bootstrap';
import JobList from '../components/jobs/JobList';
import JobFilters from '../components/jobs/JobFilters';
import { useAuth } from '../context/AuthContext';
import { getJobs } from '../services/jobs';

const JobSearch = () => {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [filters, setFilters] = useState({
    search: '',
    job_type: '',
    experience_level: '',
    location: '',
  });
  const { isAuthenticated } = useAuth();

  useEffect(() => {
    fetchJobs();
  }, [filters]);

  const fetchJobs = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      Object.entries(filters).forEach(([key, value]) => {
        if (value) params.append(key, value);
      });
      
      const data = await getJobs(params.toString());
      setJobs(data.results || data);
      setError('');
    } catch (err) {
      setError('Failed to fetch jobs');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (newFilters) => {
    setFilters(prev => ({ ...prev, ...newFilters }));
  };

  const handleSearchChange = (e) => {
    setFilters(prev => ({ ...prev, search: e.target.value }));
  };

  if (loading) {
    return (
      <div className="text-center my-5">
        <Spinner animation="border" />
        <p className="mt-2">Loading jobs...</p>
      </div>
    );
  }

  return (
    <div>
      <h1 className="mb-4">Find Your Dream Job</h1>
      
      <Row>
        <Col lg={3}>
          <JobFilters filters={filters} onChange={handleFilterChange} />
        </Col>
        
        <Col lg={9}>
          <Form className="mb-4">
            <Form.Control
              type="text"
              placeholder="Search jobs by title, company, or keyword..."
              value={filters.search}
              onChange={handleSearchChange}
              size="lg"
            />
          </Form>
          
          {error && (
            <Alert variant="danger">{error}</Alert>
          )}
          
          {jobs.length === 0 ? (
            <Alert variant="info">
              No jobs found. Try different search criteria.
            </Alert>
          ) : (
            <>
              <p className="text-muted mb-3">
                Found {jobs.length} job{jobs.length !== 1 ? 's' : ''}
              </p>
              <JobList jobs={jobs} />
            </>
          )}
        </Col>
      </Row>
    </div>
  );
};

export default JobSearch;