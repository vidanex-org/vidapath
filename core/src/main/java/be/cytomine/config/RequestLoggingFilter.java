package be.cytomine.config;

import jakarta.servlet.*;
import jakarta.servlet.http.HttpServletRequest;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.core.Ordered;
import org.springframework.core.annotation.Order;
import org.springframework.stereotype.Component;

import java.io.IOException;
import java.lang.invoke.MethodHandles;

@Component
@Order(Ordered.HIGHEST_PRECEDENCE)
public class RequestLoggingFilter implements Filter {

    private static final Logger log = LoggerFactory.getLogger(MethodHandles.lookup().lookupClass());

    @Override
    public void doFilter(ServletRequest request, ServletResponse response, FilterChain chain)
            throws IOException, ServletException {
        
        if (request instanceof HttpServletRequest) {
            HttpServletRequest httpRequest = (HttpServletRequest) request;
            long startTime = System.currentTimeMillis();
            
            // Log request entry
            log.info("[REQUEST_IN] URI: {} | METHOD: {}", httpRequest.getRequestURI(), httpRequest.getMethod());

            try {
                // Continue the filter chain
                chain.doFilter(request, response);
            } finally {
                long duration = System.currentTimeMillis() - startTime;
                // Log request exit
                log.info("[REQUEST_OUT] URI: {} | METHOD: {} | DURATION: {}ms", httpRequest.getRequestURI(), httpRequest.getMethod(), duration);
            }
        } else {
            chain.doFilter(request, response);
        }
    }

    @Override
    public void init(FilterConfig filterConfig) throws ServletException {
        // Not used
    }

    @Override
    public void destroy() {
        // Not used
    }
}
